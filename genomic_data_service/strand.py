import requests
import numpy as np


def get_matrix_file_download_url(footprint_file):
    footprint_file_url = (
        "https://www.encodeproject.org/files/" + footprint_file + "/?format=json"
    )

    data = requests.get(footprint_file_url).json()
    matrix_file_name = data["aliases"][0].split("-")[-2]

    footprint_pwms_url = (
        "https://www.encodeproject.org/search/?type=Annotation&searchTerm="
        + matrix_file_name
        + "&annotation_type=PWMs&assembly=GRCh38&field=documents&format=json"
    )
    data = requests.get(footprint_pwms_url).json()["@graph"][0]["documents"][0]
    href = data["attachment"]["href"]
    id = data["@id"]
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
    pwm = []

    for i in range(pcm.shape[0]):  # for each position i
        scores = []  # scores on each position i
        n = sum(pcm[i])  # total counts on position i
        for base in range(4):
            # assume uniform background, prob. of each base = 0.25;
            p = (pcm[i][base] + 0.25 * pseudo) / (n + pseudo)
            score = round(np.log2(p) - np.log2(0.25), 4)
            scores.append(score)
        pwm.append(scores)
    return pwm
