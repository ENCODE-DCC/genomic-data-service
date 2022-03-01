from asyncio.log import logger
import csv
import gzip
import boto3
import tempfile
from botocore.config import Config
from urllib.parse import urlparse


MAX_IN_MEMORY_FILE_SIZE = (25 * 1024 * 1024)


class FileReader():
    def __init__(self, file_path, strand_col_values={}, file_size=0, source="s3"):
        self.file_size = file_size
        self.file_path = file_path
        self.temp_file = tempfile.NamedTemporaryFile()
        self.strand_values = strand_col_values
        self.data = None
        if source == "s3":
            self.data = self.download_file_from_s3()
        elif source == "local":
            self.data = gzip.open(self.file_path, mode='rt')


    def close(self):
        if self.temp_file:
            self.temp_file.close()


    def should_load_file_in_memory(self):
        if self.file_size == 0:
            return False

        return self.file_size <= MAX_IN_MEMORY_FILE_SIZE


    def download_file_from_s3(self):
        config = Config(region_name='us-west-2', retries={'max_attempts': 2})
        s3 = boto3.client('s3', config=config)
        href = self.file_path

        parsed_href = urlparse(href, allow_fragments=False)
        s3_bucket = parsed_href.netloc
        if s3_bucket == "encode-files":
            s3_bucket = "encode-public"
        s3_path   = parsed_href.path.lstrip('/')
        if parsed_href.query:
            s3_path = parsed_href.path + '?' + parsed_href.query

        if self.should_load_file_in_memory():
            s3_response_object = s3.get_object(Bucket=s3_bucket, Key=s3_path)
            raw_data = s3_response_object['Body'].read()
            return gzip.decompress(raw_data).decode("utf-8").splitlines()
        else:
            with open(self.temp_file.name, 'wb') as f:
                s3.download_fileobj(s3_bucket, s3_path, f)
            return gzip.open(self.temp_file, mode='rt')


class SnpFileReader(FileReader):
    def parse(self):
        reader = csv.reader(self.data, delimiter='\t')
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

class RegionFileReader(FileReader):
    def parse(self):
        value_col  = self.strand_values.get('value_col')
        strand_col = self.strand_values.get('strand_col')

        reader = csv.reader(self.data, delimiter='\t')
        for row in reader:
            if row[0].startswith('#'):
                continue

            try:
                (chrom, doc) = self.region(row, value_col=value_col, strand_col=strand_col)
            except Exception:
                logger.error('%s - failure to parse row %s:%s:%s, skipping row',
                          self.file_path, row[0], row[1], row[2])
                continue

            yield (chrom, doc)


    def region(self, row, value_col=None, strand_col=None):
        chrom, start, end = row[0], int(row[1]), int(row[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }  # Stored as BED 0-based half open
        if value_col and value_col < len(row):
            doc['value'] = row[value_col]
        if strand_col:
            # Some PWMs annotation doesn't have strand info
            if strand_col < len(row) and row[strand_col] in ['.', '+', '-']:
                doc['strand'] = row[strand_col]
            # Temporary hack for Footprint data
            elif (
                strand_col - 1 < len(row)
                and row[strand_col - 1] in ['.', '+', '-']
            ):
                doc['strand'] = row[strand_col - 1]
            else:
                doc['strand'] = '.'
        return (chrom, doc)


