from asyncio.log import logger
import abc
import pickle
import py2bit

TWO_BIT_FILE_PATH = 'ml_models/two_bit_files/hg38.2bit'
GENE_LOOKUP_FILE_PATH = 'gene_lookup.pickle'
PWM_GRCH38_STRAND_COL = 3
PWM_GRCH38_SEQ_COL = 4


class Parser:
    def __init__(self, reader, cols_for_index={}, file_path=None, gene_lookup=False):
        self.reader = reader
        self.cols_for_index = cols_for_index
        self.file_path = file_path
        if gene_lookup:
            with open(GENE_LOOKUP_FILE_PATH, 'rb') as file:
                self.gene_symbol_dict = pickle.load(file)

    def parse(self):
        for line in self.reader:
            if line[0].startswith('#'):
                continue
            try:
                (chrom, doc) = self.document_generator(line)
            except Exception:
                logger.error('%s - failure to parse line %s:%s:%s, skipping line',
                             self.file_path, line[0], line[1], line[2])
                continue
            if not chrom and not doc:
                continue
            yield (chrom, doc)

    @abc.abstractmethod
    def document_generator(self, line):
        """
        This method is to used to parse one line in the given file and generate a document for elasticsearch indexing.
        It should return a tuple of chromosome and document: (chrom, doc)
        """
        return


class SnfParser(Parser):
    FREQ_TAG_START = 5
    VC_TAG_START = 3
    REF_ALLELE_COLUMN_INDEX = 5
    ALT_ALLELES_COLUMN_INDEX = 6

    def document_generator(self, line):
        chrom, start, end, rsid = line[0], int(line[1]), int(line[2]), line[3]
        if start == end:
            end = end + 1
        snp_doc = {
            'rsid': rsid,
            'chrom': chrom,
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }
        info_tags = line[8].split(';')
        freq_tag = None
        vc_tag = None
        for tag in info_tags:
            if tag.startswith('FREQ='):
                freq_tag = tag[self.FREQ_TAG_START:]
            if tag.startswith('VC='):
                vc_tag = tag[self.VC_TAG_START:]
        snp_doc['variation_type'] = vc_tag
        ref_allele = line[self.REF_ALLELE_COLUMN_INDEX]
        ref_allele_freq_map = {ref_allele: {}}
        alt_allele_freq_map = {}
        alt_alleles = line[self.ALT_ALLELES_COLUMN_INDEX].split(
            ',')
        for alt_allele in alt_alleles:
            alt_allele_freq_map[alt_allele] = {}
        if freq_tag:
            maf = 0
            for population_freq in freq_tag.split('|'):
                allele_freqs = []
                population, freqs = population_freq.split(':')
                ref_freq, *alt_freqs = freqs.split(',')
                try:
                    ref_allele_freq_map[ref_allele][population] = float(
                        ref_freq)
                    allele_freqs.append(float(ref_freq))
                except ValueError:
                    ref_allele_freq_map[ref_allele][population] = None
                for allele, freq_str in zip(alt_alleles, alt_freqs):
                    try:
                        freq = float(freq_str)
                        alt_allele_freq_map[allele][population] = freq
                        allele_freqs.append(freq)
                    except (TypeError, ValueError):
                        alt_allele_freq_map[allele][population] = None
                # maf is the 2nd most common allele frequency in a given population
                if len(allele_freqs) > 1:
                    # take the max maf across all populations
                    maf = max(maf, sorted(allele_freqs, reverse=True)[1])
            snp_doc['maf'] = maf
        snp_doc['ref_allele_freq'] = ref_allele_freq_map
        snp_doc['alt_allele_freq'] = alt_allele_freq_map
        return (chrom, snp_doc)


class RegionParser(Parser):
    def document_generator(self, line):
        chrom, start, end = line[0], int(line[1]), int(line[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }  # Stored as BED 0-based half open
        if 'value_col' in self.cols_for_index and self.cols_for_index['value_col'] < len(line):
            doc['value'] = line[self.cols_for_index['value_col']]
        if 'strand_col' in self.cols_for_index:
            # Some PWMs annotation doesn't have strand info
            if self.cols_for_index['strand_col'] < len(line) and line[self.cols_for_index['strand_col']] in ['.', '+', '-']:
                doc['strand'] = line[self.cols_for_index['strand_col']]
            # Temporary hack for Footprint data
            elif (
                self.cols_for_index['strand_col'] - 1 < len(line)
                and line[self.cols_for_index['strand_col'] - 1] in ['.', '+', '-']
            ):
                doc['strand'] = line[self.cols_for_index['strand_col'] - 1]
            else:
                doc['strand'] = '.'
        if 'ensg_id_col' in self.cols_for_index:
            ensg_id = line[self.cols_for_index['ensg_id_col']].split('.')[0]
            doc['ensg_id'] = ensg_id
            gene_name = self.gene_symbol_dict.get(ensg_id)
            if gene_name:
                doc['value'] = gene_name
            else:
                doc['value'] = line[self.cols_for_index['ensg_id_col'] + 1]
        if 'name_col' in self.cols_for_index and self.cols_for_index['name_col'] < len(line):
            doc['name'] = line[self.cols_for_index['name_col']]
        if 'p_value_col' in self.cols_for_index and self.cols_for_index['p_value_col'] < len(line):
            try:
                doc['p_value'] = float(
                    line[self.cols_for_index['p_value_col']])
            except ValueError:
                logger.error('%s - failure to parse p value in line %s:%s:%s.',
                             self.file_path, line[0], line[1], line[2])
        if 'effect_size_col' in self.cols_for_index and self.cols_for_index['effect_size_col'] < len(line):
            doc['effect_size'] = line[self.cols_for_index['effect_size_col']]
        return (chrom, doc)


class FootPrintParser(Parser):
    def __init__(self, reader, pwm, cols_for_index={}, file_path=None):
        super().__init__(reader, cols_for_index, file_path)
        self.pwm = pwm
        self.seq_reader = py2bit.open(TWO_BIT_FILE_PATH)
        self.complement = {
            'A': 'T',
            'T': 'A',
            'G': 'C',
            'C': 'G'
        }
        self.chars_index = {'A': 0, 'C': 1, 'G': 2, 'T': 3}

    def document_generator(self, line):
        chrom, start, end = line[0], int(line[1]), int(line[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }
        sequence = self.seq_reader.sequence(chrom, start, end)
        if 'N' in sequence:
            return (None, None)
        else:
            sequence_reverse_complement = ''.join(
                self.complement.get(base, base) for base in reversed(sequence))

            score = 0
            score_reverse_complement = 0

            for i in range(len(sequence)):
                score += self.pwm[i][self.chars_index[sequence[i]]]
                # add up scores for given bases on each position
                score_reverse_complement += self.pwm[i][self.chars_index[sequence_reverse_complement[i]]]
            if score >= score_reverse_complement:
                doc['strand'] = '+'
                doc['value'] = str(score)
            else:
                doc['strand'] = '-'
                doc['value'] = str(score_reverse_complement)
            return (chrom, doc)


class PWMsParser(Parser):
    def __init__(self, reader, pwm, cols_for_index={}, file_path=None):
        super().__init__(reader, cols_for_index, file_path)
        self.pwm = pwm
        self.chars_index = {'A': 0, 'C': 1, 'G': 2, 'T': 3}

    def document_generator(self, line):
        chrom, start, end = line[0], int(line[1]), int(line[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }
        doc['strand'] = line[PWM_GRCH38_STRAND_COL]
        sequence = line[PWM_GRCH38_SEQ_COL]
        score = 0
        for i in range(len(sequence)):
            score += self.pwm[i][self.chars_index[sequence[i]]]
        doc['value'] = str(score)
        return (chrom, doc)
