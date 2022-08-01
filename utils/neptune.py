from genomic_data_service.region_indexer import get_encode_accessions_from_portal, print_progress_bar, encode_graph, fetch_datasets, dataset_accession, clean_up, FILE_REQUIRED_FIELDS, DATASET_REQUIRED_FIELDS
import pickle
from genomic_data_service.region_indexer_task import metadata_doc, get_cols_for_index, SUPPORTED_CHROMOSOMES
from genomic_data_service.file_opener import S3FileOpener
from genomic_data_service.strand import get_matrix_file_download_url, get_matrix_array, get_pwm
from genomic_data_service.parser import SnfParser, RegionParser, FootPrintParser, PWMsParser
import csv
import uuid

peak_file = open('peaks_grch38_chr1.csv', 'w', newline='')
peak_writer = csv.writer(peak_file, delimiter=',')
peak_writer.writerow(['~id', 'chrom:String', 'start:Int', 'end:Int', 'file_uuid:String',
                     'strand:String', 'value:String', 'name:String', 'ensg_id:String', 'effect_size:String', '~label'])

metadata_file = open('files.csv', 'w', newline='')
file_metadata_writer = csv.writer(metadata_file, delimiter=',')
file_metadata_writer.writerow(['~id', 'file_uuid:String', 'file_id:String', 'assembly:String', 'dataset_uuid:String', 'dataset_id:String',
                              'target:String[]', 'biosample_term_name:String', 'collection_type:String', 'dataset_type:String', '~label'])

PEAK_GRCH38_CHR1 = 'peak_grch38_chr1'
FILE = 'file'


def generate_pickle():
    file_accessions = get_encode_accessions_from_portal()
    with open('file_accessions_grch38.pickle', 'wb') as f:
        pickle.dump(file_accessions, f)
    print('done!')
    return file_accessions


def write_peak(file_uuid, chrom, doc):
    # print(doc)
    id = uuid.uuid4()
    start = doc['coordinates']['gte']
    end = doc['coordinates']['lt']
    strand = doc.get('strand', '')
    value = doc.get('value', '')
    name = doc.get('name', '')
    ensg_id = doc.get('ensg_id', '')
    effect_size = doc.get('effect_size', '')
    peak_writer.writerow([id, chrom, start, end, file_uuid, strand,
                         value, name, ensg_id, effect_size, PEAK_GRCH38_CHR1])


def write_residence(metadata):
    id = metadata['uuid']
    file_uuid = metadata['uuid']
    file_id = metadata['file']['@id']
    assembly = metadata['file']['assembly']
    dataset_uuid = metadata['dataset']['uuid']
    dataset_id = metadata['dataset']['@id']
    target = metadata['dataset']['target']
    biosample_term_name = metadata['dataset']['biosample_term_name']
    collection_type = metadata['dataset']['collection_type']
    dataset_type = metadata['dataset_type']

    file_metadata_writer.writerow([id, file_uuid, file_id, assembly, dataset_uuid,
                                  dataset_id, target, biosample_term_name, collection_type, dataset_type, FILE])


def parse_file(file_uuid, file_metadata, dataset_metadata):
    metadata = metadata_doc(file_uuid, file_metadata, dataset_metadata)
    is_snp_reference = dataset_metadata['@type'][0].lower() == 'reference'
    cols_for_index = get_cols_for_index(metadata)
    file_size = file_metadata.get('file_size', 0)
    file_path = file_metadata['s3_uri']

    file_opener = S3FileOpener(file_path, file_size)
    reader = file_opener.open()
    docs = None
    if is_snp_reference:
        docs = SnfParser(reader).parse()
    elif 'ensg_id_col' in cols_for_index:
        docs = RegionParser(reader, cols_for_index,
                            file_path, gene_lookup=True).parse()
    elif file_metadata.get('annotation_type') == 'footprints' and file_metadata.get('assembly') == 'GRCh38':
        url = get_matrix_file_download_url(file_metadata['accession'])
        matrix = get_matrix_array(url)
        pwm = get_pwm(matrix)
        docs = FootPrintParser(reader, pwm, cols_for_index, file_path).parse()
    elif file_metadata.get('annotation_type') == 'PWMs' and file_metadata.get('assembly') == 'GRCh38':
        href = dataset_metadata['documents'][0]['attachment']['href']
        id = dataset_metadata['documents'][0]['@id']
        matrix_file_download_url = 'https://www.encodeproject.org' + id + href
        matrix = get_matrix_array(matrix_file_download_url)
        pwm = get_pwm(matrix)
        docs = PWMsParser(reader, pwm, cols_for_index, file_path).parse()
    else:
        docs = RegionParser(reader, cols_for_index, file_path).parse()

    for (chrom, doc) in docs:
        if chrom.lower() not in SUPPORTED_CHROMOSOMES:
            continue

        if doc['coordinates']['gte'] == doc['coordinates']['lt']:
            print(
                file_metadata['s3_uri'] + ' - on chromosome ' + doc[0] +
                ', a start coordinate ' + doc[1] + ' is ' +
                'larger than or equal to the end coordinate ' + doc[2] + ', ' +
                'skipping row'
            )
            continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz
        if chrom == 'chr1':
            write_peak(file_uuid, chrom, doc)

    file_opener.close()

    write_residence(metadata)


def index_regulome_db(encode_accessions, per_request=350):
    print('Number of files for indexing from ENCODE:', len(encode_accessions))
    datasets = {}
    chunks = [
        encode_accessions[i: i + per_request]
        for i in range(0, len(encode_accessions), per_request)
    ]
    i = 0
    print_progress_bar(i, len(chunks))
    for chunk in chunks:
        i += 1
        print_progress_bar(i, len(chunks))

        files = encode_graph([f'accession={c}' for c in chunk])

        fetch_datasets(files, datasets)

        for f in files:
            dataset = datasets.get(dataset_accession(f))

            if dataset is None:
                print(
                    f"========= No dataset {dataset_accession(f)} found for file {f['accession']}"
                )
                continue

            parse_file(
                f['uuid'],
                clean_up(f, FILE_REQUIRED_FIELDS),
                clean_up(dataset, DATASET_REQUIRED_FIELDS),

            )


def main():
    encode_accessions = generate_pickle()
    index_regulome_db(encode_accessions)
    peak_file.close()
    metadata_file.close()
    print('done')


if __name__ == '__main__':
    main()
