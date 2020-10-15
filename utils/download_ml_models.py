import os
import boto3

BUCKET_NAME = 'regulome-ml-models'
OBJECT_NAMES = ['rf_model.sav', 'bigwig_files/IC_matched_max.bw', 'bigwig_files/IC_max.bw']
LOCAL_PATH = './ml_models/'


def create_ml_directory():
    os.mkdir(LOCAL_PATH)
    os.mkdir(LOCAL_PATH + 'bigwig_files')

def models_to_download():
    if not os.path.isdir(LOCAL_PATH):
        create_ml_directory()
        return OBJECT_NAMES

    needs_downloading = []
    for filename in OBJECT_NAMES:
        if not os.path.isfile(LOCAL_PATH + filename):
            needs_downloading.append(filename)

    return needs_downloading

def download_models(needs_downloading):
    s3 = boto3.client('s3')

    for filename in needs_downloading:
        with open(LOCAL_PATH + filename, 'wb+') as f:
            print("Downloading " + filename + " ...")
            s3.download_fileobj(BUCKET_NAME, filename, f)

def main():
    needs_downloading = models_to_download()

    if len(needs_downloading) == 0:
        print("ML models already downloaded.")
        return

    download_models(needs_downloading)

    print("ML models downloaded successfully.")


if __name__ == '__main__':
    main()
