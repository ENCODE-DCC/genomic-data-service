from asyncio.log import logger
import abc
import pickle
import py2bit

class Parser:
    def __init__(self, reader, cols_for_index={}, file_path=None, pwm=None,gene_lookup=False):
        self.reader = reader
        self.cols_for_index = cols_for_index
        self.file_path = file_path
        if pwm:
            self.pwm = pwm
            self.seq_reader = py2bit.open("hg38.2bit")
            self.base_paris = {
                'A': 'T',
                'T': 'A',
                'G': 'C',
                'C': 'G'
                }
            self.chars_index = {'A':0,'C':1,'G':2,'T':3}
        if gene_lookup:
            with open("gene_lookup.pickle", "rb") as file:
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
            yield (chrom, doc)  
    @abc.abstractmethod
    def document_generator(self, line):
        """
        This method is to used to parse one line in the given file and generate a document for elasticsearch indexing.
        It should return a tuple of chromosome and document: (chrom, doc)
        """
        return

class SnfParser(Parser):
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
        try:
            freq_tag = [
                tag for tag in info_tags if tag.startswith('FREQ=')
            ][0][5:]
        except IndexError:
            freq_tag = None
        if freq_tag:
            ref_allele_freq_map = {line[5]: {}}
            alt_alleles = line[6].split(',')
            alt_allele_freq_map = {}
            alt_allele_freqs = set()
            for population_freq in freq_tag.split('|'):
                population, freqs = population_freq.split(':')
                ref_freq, *alt_freqs = freqs.split(',')
                try:
                    ref_allele_freq_map[line[5]][population] = float(ref_freq)
                except ValueError:
                    pass
                for allele, freq_str in zip(alt_alleles, alt_freqs):
                    alt_allele_freq_map.setdefault(allele, {})
                    try:
                        freq = float(freq_str)
                    except (TypeError, ValueError):
                        continue
                    alt_allele_freqs.add(freq)
                    alt_allele_freq_map[allele][population] = freq
            snp_doc['ref_allele_freq'] = ref_allele_freq_map
            snp_doc['alt_allele_freq'] = alt_allele_freq_map
            if alt_allele_freqs:
                snp_doc['maf'] = max(alt_allele_freqs)
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
            doc['value'] = line[self.cols_for_index['value_col'] ]
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
        if 'name_col' in self.cols_for_index and self.cols_for_index['name_col'] < len(line):
            doc['name'] = line[self.cols_for_index['name_col']]
        if 'p_value_col' in self.cols_for_index and self.cols_for_index['p_value_col'] < len(line):
            doc['p_value'] = line[self.cols_for_index['p_value_col']]
        if 'effect_size_col' in self.cols_for_index and self.cols_for_index['effect_size_col'] < len(line):
            doc['effect_size'] = line[self.cols_for_index['effect_size_col']]
        return (chrom, doc)

class FootPrintParser(Parser):
    def document_generator(self, line):
        chrom, start, end = line[0], int(line[1]), int(line[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }
        sequence_5_to_3 = self.seq_reader.sequence(chrom, start, end)
        sequence_3_to_5 = ''
        for base in sequence_5_to_3:
            sequence_3_to_5 += self.base_paris[base]

        score_5_to_3 = 0
        score_3_to_5 = 0

        for i in range(len(sequence_5_to_3)):
            score_5_to_3 += self.pwm[i][self.chars_index[sequence_5_to_3[i]]]
            score_3_to_5 += self.pwm[i][self.chars_index[sequence_3_to_5[i]]] #add up scores for given bases on each position
        if score_5_to_3 >= score_3_to_5:
            doc['strand'] = '+'
        else:
            doc['strand'] = '-'
        return (chrom, doc)
