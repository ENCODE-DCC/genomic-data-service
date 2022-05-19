from genomic_data_service.strand import (
    get_matrix_file_download_url,
    get_matrix_array,
    get_pwm,
)
import numpy as np


def test_get_matrix_file_download_url(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "aliases": [
            "j-michael-cherry:regulomeDB-Files-TRACE-Footprints-MA0125.1-ENCFF642YJJ"
        ],
        "@graph": [
            {
                "documents": [
                    {
                        "@id": "/documents/fcc8d285-b294-45e9-8a17-12e4deb1599d/",
                        "attachment": {"href": "@@download/attachment/MA0125.1.txt"},
                    }
                ]
            }
        ],
    }
    mocker.patch("genomic_data_service.strand.requests.get", return_value=mock_response)
    url = get_matrix_file_download_url("ENCFF300WPY")
    assert (
        url
        == "https://www.encodeproject.org/documents/fcc8d285-b294-45e9-8a17-12e4deb1599d/@@download/attachment/MA0125.1.txt"
    )


def test_get_matrix_array(mocker):
    mock_response = mocker.Mock()
    mock_response.text = (
        ">MA0125.1\tNobox\n"
        "A  [     0     36     38      1      2     15      4      2 ]\n"
        "C  [     1      0      0      1      0      0     12     13 ]\n"
        "G  [     0      0      0      2      4     22     18      6 ]\n"
        "T  [    37      2      0     34     32      1      4     17 ]\n"
    )
    mocker.patch("genomic_data_service.strand.requests.get", return_value=mock_response)
    matrix_file_download_url = "https://www.encodeproject.org/documents/fcc8d285-b294-45e9-8a17-12e4deb1599d/@@download/attachment/MA0125.1.txt"
    matrix = get_matrix_array(matrix_file_download_url)
    assert matrix.tolist() == [
        [0.0, 1.0, 0.0, 37.0],
        [36.0, 0.0, 0.0, 2.0],
        [38.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 2.0, 34.0],
        [2.0, 0.0, 4.0, 32.0],
        [15.0, 0.0, 22.0, 1.0],
        [4.0, 12.0, 18.0, 4.0],
        [2.0, 13.0, 6.0, 17.0],
    ]


def test_get_pwm():
    pcm = np.array(
        [
            [0.0, 1.0, 0.0, 37.0],
            [36.0, 0.0, 0.0, 2.0],
            [38.0, 0.0, 0.0, 0.0],
            [1.0, 1.0, 2.0, 34.0],
            [2.0, 0.0, 4.0, 32.0],
            [15.0, 0.0, 22.0, 1.0],
            [4.0, 12.0, 18.0, 4.0],
            [2.0, 13.0, 6.0, 17.0],
        ]
    )
    pwm = get_pwm(pcm)
    assert pwm == [
        [-5.2854, -2.9635, -5.2854, 1.9338],
        [1.8945, -5.2854, -5.2854, -2.1155],
        [1.972, -5.2854, -5.2854, -5.2854],
        [-2.9635, -2.9635, -2.1155, 1.8126],
        [-2.1155, -5.2854, -1.1979, 1.7258],
        [0.6453, -5.2854, 1.1903, -2.9635],
        [-1.1979, 0.3293, 0.9044, -1.1979],
        [-2.1155, 0.4425, -0.6415, 0.8231],
    ]