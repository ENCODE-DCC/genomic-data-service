import requests
import numpy as np
from pytfmpval import tfmp
import logging



def get_matrix_file_download_url(dataset_metadata):
    documents = dataset_metadata['documents']
    try: 
        document = documents[0]
    except IndexError:
        logging.error("Missing documents for dataset: %s", dataset_metadata["accession"])
        raise
    href = document["attachment"]["href"]
    id = document["@id"]
    matrix_file_download_url = "https://www.encodeproject.org" + id + href
    return matrix_file_download_url


# get position count matrix
def get_matrix_array(matrix_file_download_url):
    data = requests.get(matrix_file_download_url).text.splitlines()[1:]
    # Creates a row X col list, all set to 0
    row = len(data[0].split()[2:-1])
    matrix = np.zeros((row, 4))
    for i in range(4):
        line_list = data[i].split()[2:-1]
        line_list = [int(i) for i in line_list]
        for j in range(len(line_list)):
            matrix[j][i] = line_list[j]
    return matrix


#  calculate position weight matrix from position count matrix in log2 scale
def get_pwm(pcm, pseudo=1):
    pwm = np.zeros_like(pcm)
    for i in range(pcm.shape[0]):  # for each position i
        n = sum(pcm[i])  # total counts on position i
        for base in range(4):
            # assume uniform background, prob. of each base = 0.25;
            p = (pcm[i][base] + 0.25 * pseudo) / (n + pseudo)
            score = round(np.log2(p) - np.log2(0.25), 4)
            pwm[i][base] = score
    return pwm

def get_p_value(pwm, score):
    pwm = np.transpose(pwm)
    pwm = pwm.flatten().tolist()
    pwm_str = [str(count) for count in pwm]
    pwm_str = ' '.join(pwm_str)
    matrix = tfmp.read_matrix(pwm_str, mat_type='pwm', log_type='log2')
    p_value = tfmp.score2pval(matrix, score)
    return p_value
