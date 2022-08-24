import boto3
from pathlib import Path

BUCKET_NAME = 'regulome-ml-models'
OBJECT_NAMES = ['rf_model1.0.1.sav', 'bigwig_files/IC_matched_max.bw',
                'bigwig_files/IC_max.bw', 'bigwig_files/IC_matched_max_GRCh38.bw', 'bigwig_files/IC_max_GRCh38.bw', 'two_bit_files/hg38.2bit', 'two_bit_files/hg19.2bit']
LOCAL_DIR = Path('./ml_models/')
BIGWIG_DIR = LOCAL_DIR.joinpath('bigwig_files')
TWOBIT_DIR = LOCAL_DIR.joinpath('two_bit_files')
DIRS = [LOCAL_DIR, BIGWIG_DIR, TWOBIT_DIR]
OBJECT_PATHS = [LOCAL_DIR.joinpath(path) for path in OBJECT_NAMES]
PATH_TO_S3_KEY = {Path('./ml_models/rf_model1.0.1.sav'): 'rf_model1.0.1.sav',
                  Path('./ml_models/bigwig_files/IC_matched_max.bw'): 'bigwig_files/IC_matched_max.bw',
                  Path('./ml_models/bigwig_files/IC_max.bw'): 'bigwig_files/IC_max.bw',
                  Path('./ml_models/bigwig_files/IC_matched_max_GRCh38.bw'): 'bigwig_files/IC_matched_max_GRCh38.bw',
                  Path('./ml_models/bigwig_files/IC_max_GRCh38.bw'): 'bigwig_files/IC_max_GRCh38.bw',
                  Path('./ml_models/two_bit_files/hg38.2bit'): 'two_bit_files/hg38.2bit',
                  Path('./ml_models/two_bit_files/hg19.2bit'): 'two_bit_files/hg19.2bit', }


def create_directories(dirs):
    '''
    Create directories if they don't already exist.
    dirs: iterable of Path objects
    '''
    for directory in dirs:
        if not directory.exists():
            directory.mkdir()


def models_to_download(paths_to_check):
    '''
    Check paths and return ones that do not exist.
    paths_to_check: iterable of Path objects
    returns: list of Path objects
    '''
    needs_downloading = []
    for path in paths_to_check:
        if not path.exists():
            needs_downloading.append(path)
    return needs_downloading


def download_models(needs_downloading):
    s3 = boto3.client('s3')
    for file_ in needs_downloading:
        with open(file_, 'wb+') as f:
            print('Downloading ' + str(file_) + ' ...')
            s3.download_fileobj(BUCKET_NAME, PATH_TO_S3_KEY[file_], f)


def main():
    create_directories(DIRS)
    needs_downloading = models_to_download(OBJECT_PATHS)

    if len(needs_downloading) == 0:
        print('Files already downloaded.')
        return

    download_models(needs_downloading)

    print('Files downloaded successfully.')


if __name__ == '__main__':
    main()
