from asyncio.log import logger
import abc

class Parser:
    def __init__(self, reader, value_col=None, strand_col=None):
        self.reader = reader
        self.value_col = value_col
        self.strand_col = strand_col
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
    def document_generator(self, line, value_col=None, strand_col=None):
        chrom, start, end = line[0], int(line[1]), int(line[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }  # Stored as BED 0-based half open
        if self.value_col and self.value_col < len(line):
            doc['value'] = line[self.value_col]
        if self.strand_col:
            # Some PWMs annotation doesn't have strand info
            if self.strand_col < len(line) and line[self.strand_col] in ['.', '+', '-']:
                doc['strand'] = line[self.strand_col]
            # Temporary hack for Footprint data
            elif (
                self.strand_col - 1 < len(line)
                and line[self.strand_col - 1] in ['.', '+', '-']
            ):
                doc['strand'] = line[self.strand_col - 1]
            else:
                doc['strand'] = '.'
        return (chrom, doc)
