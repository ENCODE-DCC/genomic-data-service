import csv
import gzip
import boto3
import tempfile
from botocore import UNSIGNED
from botocore.config import Config
from urllib.parse import urlparse
import abc

MAX_IN_MEMORY_FILE_SIZE = (25 * 1024 * 1024)

class FileOpener:
    def __init__(self, file_path, file_size=0):
        self.file_size = file_size
        self.file_path = file_path
        self.temp_file = None

    def close(self):
        if self.temp_file:
            self.temp_file.close()

    @abc.abstractmethod
    def open(self):
        """
        This method is to return a reader object which will iterate over lines in the given file
        """

class S3FileOpener(FileOpener):

    def should_load_file_in_memory(self):
        # if file size is 0, we treat it as a big file, then we shouldn't load file in memory.
        if self.file_size == 0:
            return False
        return self.file_size <= MAX_IN_MEMORY_FILE_SIZE

    def open(self):
        config = Config(region_name='us-west-2', retries={'max_attempts': 2}, signature_version=UNSIGNED)
        s3 = boto3.client('s3', config=config)
        href = self.file_path

        parsed_href = urlparse(href, allow_fragments=False)
        s3_bucket = parsed_href.netloc
        if s3_bucket == "encode-files":
            s3_bucket = "encode-public"
        s3_path = parsed_href.path.lstrip('/')
        if parsed_href.query:
            s3_path = parsed_href.path + '?' + parsed_href.query
        file = None
        if self.should_load_file_in_memory():
            s3_response_object = s3.get_object(Bucket=s3_bucket, Key=s3_path)
            raw_data = s3_response_object['Body'].read()
            file = gzip.decompress(raw_data).decode("utf-8").splitlines()
        else:
            self.temp_file = tempfile.NamedTemporaryFile()
            with open(self.temp_file.name, 'wb') as f:
                s3.download_fileobj(s3_bucket, s3_path, f)
            file = gzip.open(self.temp_file, mode='rt')

        file_reader = csv.reader(file, delimiter='\t')
        return file_reader

class LocalFileOpener(FileOpener):
    def open(self):
        file = gzip.open(self.file_path, mode='rt')
        file_reader = csv.reader(file, delimiter='\t')
        return file_reader


