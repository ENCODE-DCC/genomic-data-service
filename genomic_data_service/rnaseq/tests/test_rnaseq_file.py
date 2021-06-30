import pytest


def test_rnaseq_file_init(raw_files):
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    rna_file = RnaSeqFile(raw_files[0])
    assert isinstance(rna_file, RnaSeqFile)
    assert rna_file.props == raw_files[0]


def test_rnaseq_file_url(raw_files):
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    rna_file = RnaSeqFile(raw_files[0])
    assert (
        rna_file.url == 'https://www.encodeproject.org/files/ENCFF241WYH/@@download/ENCFF241WYH.tsv'
    )


def test_rnaseq_file_path(raw_files):
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    rna_file = RnaSeqFile(raw_files[0])
    assert rna_file.path == '/tmp/ENCFF241WYH.tsv'


def test_rnaseq_file_get_expressions(raw_files, raw_expressions, mocker):
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    rna_file = RnaSeqFile(raw_files[0])
    mocker.patch(
        'genomic_data_service.rnaseq.domain.file.get_expression_generator',
        return_value=raw_expressions,
    )
    expressions = list(rna_file._get_expressions())
    assert len(expressions) == 4
    assert expressions[0].gene_id == 'ENSG00000034677.12'
    assert expressions[1].transcript_ids == 'ENST00000042931.1,ENST00000549706.5,ENST00000552539.1,ENST00000553030.5'
    assert expressions[2].tpm == 0.27
    assert expressions[3].fpkm == 15.8


def test_rnaseq_file_get_indices_from_header():
    from genomic_data_service.rnaseq.domain.file import get_indices_from_header
    header = [
        'gene_id',
        'transcript_id(s)',
        'length',
        'effective_length',
        'expected_count',
        'TPM',
        'FPKM',
        'posterior_mean_count',
        'posterior_standard_deviation_of_count',
        'pme_TPM',
        'pme_FPKM',
        'TPM_ci_lower_bound',
        'TPM_ci_upper_bound',
        'TPM_coefficient_of_quartile_variation',
        'FPKM_ci_lower_bound',
        'FPKM_ci_upper_bound',
        'FPKM_coefficient_of_quartile_variation',
    ]
    assert get_indices_from_header(header) == [0, 1, 5, 6]


def test_rnaseq_file_get_values_from_row():
    from genomic_data_service.rnaseq.domain.file import get_values_from_row
    row = [0, 1, 2, 3, 4, 5]
    assert get_values_from_row(row, [0, 2, 5]) == [0, 2, 5]


def test_rnaseq_file_get_expression_generator(local_quantification_tsv_path):
    from genomic_data_service.rnaseq.domain.file import get_expression_generator
    expressions = get_expression_generator(
        '',
        local_quantification_tsv_path
    )
    assert list(expressions) == [
        ['ENSG00000150873.11', 'ENST00000381585.7,ENST00000405022.3', '0.01', '0.02'],
        ['ENSG00000150893.10', 'ENST00000280481.8,ENST00000482551.1', '3.02', '4.69'],
        ['ENSG00000150907.7', 'ENST00000379561.5,ENST00000473775.1,ENST00000636651.1', '2.73', '4.23'],
        ['ENSG00000150938.9', 'ENST00000280527.6,ENST00000413985.1,ENST00000426856.1,ENST00000428774.1,ENST00000473403.5,ENST00000477491.5,ENST00000481321.1,ENST00000497236.1', '4.52', '7.01'],
        ['ENSG00000150961.14', 'ENST00000280551.10,ENST00000419654.6,ENST00000502526.1,ENST00000502830.1,ENST00000503683.1,ENST00000505134.5,ENST00000505280.1,ENST00000506622.5,ENST00000509818.5,ENST00000511033.1,ENST00000511481.5,ENST00000511715.1,ENST00000514418.1,ENST00000514561.5', '8.65', '13.42'],
        ['ENSG00000150967.17', 'ENST00000280560.12,ENST00000344275.11,ENST00000346530.9,ENST00000392439.7,ENST00000426173.6,ENST00000442028.6,ENST00000442833.6,ENST00000536976.5,ENST00000537276.5,ENST00000538895.5,ENST00000540285.5,ENST00000540971.5,ENST00000541424.1,ENST00000541983.1,ENST00000542448.5,ENST00000542678.5,ENST00000543935.1,ENST00000545373.1,ENST00000546077.1,ENST00000546289.5,ENST00000622723.1', '0.96', '1.49'],
        ['ENSG00000150977.10', 'ENST00000280571.9', '0.21', '0.32'],
        ['ENSG00000150990.7', 'ENST00000308736.6,ENST00000507267.2,ENST00000539298.1,ENST00000542400.5,ENST00000543962.1,ENST00000544745.1', '1.60', '2.48'],
        ['ENSG00000150991.14', 'ENST00000339647.5,ENST00000535131.1,ENST00000535859.1,ENST00000536661.1,ENST00000536769.1,ENST00000538617.5,ENST00000540351.1,ENST00000540700.1,ENST00000541272.1,ENST00000541645.1,ENST00000542416.1,ENST00000544481.1,ENST00000546120.2,ENST00000546271.1', '183.38', '284.55'],
        ['ENSG00000150995.19', 'ENST00000302640.12,ENST00000354582.11,ENST00000357086.10,ENST00000443694.4,ENST00000456211.8,ENST00000463980.6,ENST00000467056.6,ENST00000467545.6,ENST00000472205.1,ENST00000477577.2,ENST00000478515.2,ENST00000479831.1,ENST00000481415.2,ENST00000487016.1,ENST00000490572.1,ENST00000491868.2,ENST00000493491.6,ENST00000494681.5,ENST00000544951.6,ENST00000647624.1,ENST00000647673.1,ENST00000647685.1,ENST00000647708.1,ENST00000647717.1,ENST00000647900.1,ENST00000647997.1,ENST00000648016.1,ENST00000648038.1,ENST00000648208.1,ENST00000648212.1,ENST00000648266.1,ENST00000648309.1,ENST00000648390.1,ENST00000648431.1,ENST00000648510.1,ENST00000648564.1,ENST00000648770.1,ENST00000649015.1,ENST00000649051.1,ENST00000649139.1,ENST00000649144.1,ENST00000649272.1,ENST00000649314.1,ENST00000649414.1,ENST00000649425.1,ENST00000649430.1,ENST00000649669.1,ENST00000649694.1,ENST00000649767.1,ENST00000649908.1,ENST00000650074.1,ENST00000650079.1,ENST00000650139.1,ENST00000650146.1,ENST00000650294.1,ENST00000650552.1', '5.82', '9.04']
    ]


def test_rnaseq_file_get_expressions_local_file(local_quantification_tsv_path):
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    from genomic_data_service.rnaseq.domain.expression import Expression
    file_name = local_quantification_tsv_path.split('/')[-1]
    base_path = local_quantification_tsv_path.replace(file_name, '')
    props = {
        'href': '/files/ENCFF241WYH/@@download/ENCFF241WYH.tsv',
    }
    rna_file = RnaSeqFile(props)
    rna_file.BASE_PATH = base_path
    rna_file.DOMAIN = ''
    expressions = list(rna_file._get_expressions())
    assert len(expressions) == 10
    assert expressions[0] == Expression(
        *[
            'ENSG00000150873.11',
            'ENST00000381585.7,ENST00000405022.3',
            '0.01',
            '0.02'
        ]
    )


@pytest.mark.skip(reason='This actually downloads a file')
def test_rnaseq_file_get_expressions_remote_file():
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    from genomic_data_service.rnaseq.domain.expression import Expression
    props = {
        'href': '/files/ENCFF241WYH/@@download/ENCFF241WYH.tsv',
    }
    rna_file = RnaSeqFile(props)
    expressions = list(rna_file._get_expressions())
    assert len(expressions) == 59526
    assert expressions[0] == Expression(
        *[
            '10904',
            '10904',
            '0.00',
            '0.00'
        ]
    )


def test_rnaseq_file_extract_file_properties(raw_files):
    from genomic_data_service.rnaseq.domain.file import RnaSeqFile
    rna_file = RnaSeqFile(raw_files[0])
    rna_file._extract_file_properties()
    assert rna_file._file_properties == {
        '@id': '/files/ENCFF241WYH/',
        'assay_title': 'polyA plus RNA-seq',
        'assembly': 'GRCh38',
        'biosample_ontology': {
            'organ_slims': [
                'musculature of body'
            ],
            'term_name': 'muscle of trunk',
            'synonyms': [
                'torso muscle organ',
                'trunk musculature',
                'trunk muscle',
                'muscle of trunk',
                'muscle organ of torso',
                'trunk muscle organ',
                'muscle organ of trunk',
                'body musculature'
            ],
            'name': 'tissue_UBERON_0001774',
            'term_id': 'UBERON:0001774',
            'classification': 'tissue'
        },
        'dataset': '/experiments/ENCSR906HEV/',
        'donors': [
            '/human-donors/ENCDO676JUB/'
        ],
        'genome_annotation': 'V29',
    }
