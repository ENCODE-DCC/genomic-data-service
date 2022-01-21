from asyncio.log import logger
import csv
import gzip


class LocalReader():
    def __init__(self, file_path):      
        self.file_path = file_path
        self.file = gzip.open(self.file_path, mode='rt')


    def parse(self):

        reader = csv.reader(self.file, delimiter='\t')
        for row in reader:
            if row[0].startswith('#'):
                continue

            try:
                (chrom, doc) = self.snp(row)
           
            except Exception:
                logger.error('%s - failure to parse row %s:%s:%s, skipping row',
                          self.file_path, row[0], row[1], row[2])
                continue

            yield (chrom, doc)


    def snp(self, row):
        chrom, start, end, rsid = row[0], int(row[1]), int(row[2]), row[3]
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
        info_tags = row[8].split(';')
        try:
            freq_tag = [
                tag for tag in info_tags if tag.startswith('FREQ=')
            ][0][5:]
        except IndexError:
            freq_tag = None
        if freq_tag:
            ref_allele_freq_map = {row[5]: {}}
            alt_alleles = row[6].split(',')
            alt_allele_freq_map = {}
            alt_allele_freqs = set()
            for population_freq in freq_tag.split('|'):
                population, freqs = population_freq.split(':')
                ref_freq, *alt_freqs = freqs.split(',')
                try:
                    ref_allele_freq_map[row[5]][population] = float(ref_freq)
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
