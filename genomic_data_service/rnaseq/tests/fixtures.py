import pytest

@pytest.fixture
def as_expressions():
    return [
        {
            "annotation": "GRCh38",
            "assayType": "shRNA knockdown followed by RNA-seq",
            "biosample_classification": "cell line",
            "biosample_organ": "exocrine gland, epithelium, liver, endocrine gland",
            "biosample_sex": "male",
            "biosample_summary": "Homo sapiens HepG2 cell line expressing RNAi targeting GNB2L1",
            "biosample_system": "digestive system, endocrine system, exocrine system",
            "biosample_term_name": "HepG2",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF007FIZ",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR116YMU",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR116YMU",
            "tpm": "70.00"
        },
        {
            "annotation": "GRCh38",
            "assayType": "CRISPR genome editing followed by RNA-seq",
            "biosample_classification": "cell line",
            "biosample_organ": "blood, bodily fluid",
            "biosample_sex": "female",
            "biosample_summary": "Homo sapiens K562 cell line genetically modified (deletion) using CRISPR targeting FXR2",
            "biosample_system": "immune system",
            "biosample_term_name": "K562",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF006ECV",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR376GHG",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR376GHG",
            "tpm": "38.10"
        },
        {
            "annotation": "GRCh38",
            "assayType": "polyA plus RNA-seq",
            "biosample_classification": "tissue",
            "biosample_organ": "musculature of body, limb",
            "biosample_sex": "unknown",
            "biosample_summary": "Homo sapiens embryo (101 days) muscle of arm tissue",
            "biosample_system": "musculature",
            "biosample_term_name": "muscle of arm",
            "encodeID": "/genes/51442/",
            "expressionID": "ENCFF007LRI",
            "featureID": "ENSG00000102243.12",
            "gene_name": "vestigial like family member 1",
            "gene_symbol": "VGLL1",
            "libraryPrepProtocol": "https://www.encodeproject.org/ENCSR677MYO",
            "samplePrepProtocol": "https://www.encodeproject.org/ENCSR677MYO",
            "tpm": "1.40"
        },
    ]


@pytest.fixture
def raw_files():
    return [
        {
            "@id": "/files/ENCFF241WYH/",
            "@type": ["File", "Item"],
            "assay_title": "polyA plus RNA-seq",
            "assembly": "GRCh38",
            "biosample_ontology": {
                "organ_slims": [
                    "musculature of body"
                ],
                "term_name": "muscle of trunk",
                "synonyms": [
                    "torso muscle organ",
                    "trunk musculature",
                    "trunk muscle",
                    "muscle of trunk",
                    "muscle organ of torso",
                    "trunk muscle organ",
                    "muscle organ of trunk",
                    "body musculature"
                ],
                "name": "tissue_UBERON_0001774",
                "term_id": "UBERON:0001774",
                "classification": "tissue"
            },
            "dataset": "/experiments/ENCSR906HEV/",
            "donors": [
                "/human-donors/ENCDO676JUB/"
            ],
            "file_type": "tsv",
            "genome_annotation": "V29",
            "href": "/files/ENCFF241WYH/@@download/ENCFF241WYH.tsv",
            "md5sum": "9e5f83679959b379501794bac3d07776",
            "output_type": "gene quantifications",
            "s3_uri": "s3://encode-public/2021/06/03/6cabf466-2eff-49ec-ad26-59ea821c3457/ENCFF241WYH.tsv",
            "title": "ENCFF241WYH"
        },
        {
            "@id": "/files/ENCFF273KTX/",
            "@type": ["File", "Item"],
            "assay_title": "total RNA-seq",
            "assembly": "GRCh38",
            "biosample_ontology": {
                "organ_slims": [
                    "uterus"
                ],
                "term_name": "uterus",
                "synonyms": [],
                "name": "tissue_UBERON_0000995",
                "term_id": "UBERON:0000995",
                "classification": "tissue"
            },
            "dataset": "/experiments/ENCSR113HQM/",
            "donors": ["/human-donors/ENCDO793LXB/"],
            "file_type": "tsv",
            "genome_annotation": "V29",
            "href": "/files/ENCFF273KTX/@@download/ENCFF273KTX.tsv",
            "md5sum": "b5533f4fb7823d0668b6cd29f8a203db",
            "output_type": "gene quantifications",
            "s3_uri": "s3://encode-public/2021/06/03/e1864121-4fee-4502-a622-28b9bf03acc7/ENCFF273KTX.tsv",
            "title": "ENCFF273KTX"
        },
        {
            "@id": "/files/ENCFF106SZG/",
            "@type": ["File", "Item"],
            "assay_title": "total RNA-seq",
            "assembly": "GRCh38",
            "biosample_ontology": {
                "organ_slims": [
                    "skin of body"
                ],
                "term_name": "GM23338",
                "synonyms": [],
                "name": "cell_line_EFO_0007950",
                "term_id": "EFO:0007950",
                "classification": "cell line"
            },
            "dataset": "/experiments/ENCSR938LSP/",
            "donors": [
                "/human-donors/ENCDO336AAA/"
            ],
            "file_type": "tsv",
            "genome_annotation": "V29",
            "href": "/files/ENCFF106SZG/@@download/ENCFF106SZG.tsv",
            "md5sum": "e0b797e4f0f03f1f0ae96d2bafaa317a",
            "output_type": "gene quantifications",
            "s3_uri": "s3://encode-public/2021/06/02/0e42faa0-5e20-4847-8dab-4a836adb4f1c/ENCFF106SZG.tsv",
            "title": "ENCFF106SZG"
        },
        {
            "@id": "/files/ENCFF730OTJ/",
            "@type": ["File", "Item"],
            "assay_title": "total RNA-seq",
            "assembly": "GRCh38",
            "biosample_ontology": {
                "organ_slims": [
                    "skin of body"
                ],
                "term_name": "GM23338",
                "synonyms": [],
                "name": "cell_line_EFO_0007950",
                "term_id": "EFO:0007950",
                "classification": "cell line"
            },
            "dataset": "/experiments/ENCSR938LSP/",
            "donors": [
                "/human-donors/ENCDO336AAA/"
            ],
            "file_type": "tsv",
            "genome_annotation": "V29",
            "href": "/files/ENCFF730OTJ/@@download/ENCFF730OTJ.tsv",
            "md5sum": "0ce5c349e4992f72c5c9343cbcc06d9d",
            "output_type": "gene quantifications",
            "s3_uri": "s3://encode-public/2021/06/02/69e7696a-be3b-454d-8548-5ad685129bc8/ENCFF730OTJ.tsv",
            "title": "ENCFF730OTJ"
        }
    ]


@pytest.fixture
def files(raw_files):
    from genomic_data_service.rna_seq.domain.file import RnaSeqFile
    return [
        RnaSeqFile(props=raw_file)
        for raw_file in raw_files
    ]


@pytest.fixture
def raw_expressions():
    return [
        [
            'ENSG00000034677.12',
            'ENST00000341084.6,ENST00000432381.2,ENST00000517584.5,ENST00000519342.1,ENST00000519449.5,ENST00000519527.5,ENST00000520071.1,ENST00000520903.1,ENST00000522182.1,ENST00000522369.5,ENST00000523167.1,ENST00000523255.5,ENST00000523481.5,ENST00000523644.1,ENST00000524233.1',
            9.34,
            14.49
        ],
        [
            'ENSG00000039987.6',
            'ENST00000042931.1,ENST00000549706.5,ENST00000552539.1,ENST00000553030.5',
            0.01,
            0.02
        ],
        [
            'ENSG00000055732.12',
            'ENST00000341115.8,ENST00000370587.5,ENST00000370589.6,ENST00000474447.1,ENST00000475312.1,ENST00000490600.6',
            0.27,
            0.41
        ],
        [
            'ENSG00000060982.14',
            'ENST00000261192.11,ENST00000342945.9,ENST00000355164.3,ENST00000538118.5,ENST00000539282.5,ENST00000539780.5,ENST00000543099.1,ENST00000544418.1,ENST00000546285.1,ENST00000612790.1',
            10.18,
            15.8
        ],
    ]


@pytest.fixture
def expressions(raw_expressions):
    from genomic_data_service.rnaseq.domain.expression import Expression
    return [
        Expression(*raw_expression)
        for raw_expression in raw_expressions
    ]


@pytest.fixture
def raw_human_genes():
    return [
        {
            "@id": "/genes/100302691/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "HGNC:37192",
                "RefSeq:NR_033927.1",
                "ENSEMBL:ENSG00000224939"
            ],
            "geneid": "100302691",
            "name": "long intergenic non-protein coding RNA 184",
            "organism": {
                "scientific_name": "Homo sapiens"
            },
            "symbol": "LINC00184",
            "synonyms": [
                "HANC",
                "NCRNA00184"
            ],
            "title": "LINC00184 (Homo sapiens)"
        },
        {
            "@id": "/genes/100302145/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "ENSEMBL:ENSG00000283857",
                "miRBase:MI0006382",
                "RefSeq:NR_031649.1",
                "HGNC:35313"
            ],
            "geneid": "100302145",
            "name": "microRNA 1247",
            "organism": {
                "scientific_name": "Homo sapiens"
            },
            "symbol": "MIR1247",
            "synonyms": [
                "MIRN1247",
                "hsa-mir-1247",
                "mir-1247"
            ],
            "title": "MIR1247 (Homo sapiens)"
        },
        {
            "@id": "/genes/100289092/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "RefSeq:NR_046290.1",
                "HGNC:51370",
                "ENSEMBL:ENSG00000260442"
            ],
            "geneid": "100289092",
            "name":"ATP2A1 antisense RNA 1",
            "organism": {
                "scientific_name": "Homo sapiens"
            },
            "symbol": "ATP2A1-AS1",
            "title": "ATP2A1-AS1 (Homo sapiens)"
        },
        {
            "@id": "/genes/100302286/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "ENSEMBL:ENSG00000221650",
                "miRBase:MI0006404",
                "RefSeq:NR_031671.1",
                "HGNC:35335"
            ],
            "geneid": "100302286",
            "name": "microRNA 1267",
            "organism": {
                "scientific_name": "Homo sapiens"
            },
            "symbol": "MIR1267",
            "synonyms": [
                "MIRN1267",
                "hsa-mir-1267"
            ],
            "title": "MIR1267 (Homo sapiens)"
        }
    ]


@pytest.fixture
def raw_mouse_genes():
    return [
        {
            "@id": "/genes/319178/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "Vega:OTTMUSG00000000581",
                "ENSEMBL:ENSMUSG00000075031",
                "RefSeq:NM_175664.3",
                "MGI:2448377",
                "UniProtKB:Q64475",
                "RefSeq:NM_175664.2"
            ],
            "geneid": "319178",
            "name": "histone cluster 1, H2bb",
            "organism": {
                "scientific_name": "Mus musculus"
            },
            "symbol": "Hist1h2bb",
            "synonyms": [
                "H2b-143"
            ],
            "title": "Hist1h2bb (Mus musculus)"
        },
        {
            "@id": "/genes/258862/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "ENSEMBL:ENSMUSG00000047868",
                "RefSeq:NM_146863.1",
                "Vega:OTTMUSG00000056483",
                "MGI:3030604",
                "UniProtKB:Q8VGC2"
            ],
            "geneid": "258862",
            "name": "olfactory receptor 770",
            "organism": {
                "scientific_name": "Mus musculus"
            },
            "symbol": "Olfr770",
            "synonyms": [
                "MOR114-5"
            ],
            "title": "Olfr770 (Mus musculus)"
        },
        {
            "@id": "/genes/239096/",
            "@type": ["Gene", "Item"],
            "dbxrefs": [
                "UniProtKB:Q6PFX6",
                "MGI:1928330",
                "RefSeq:NM_199470.2",
                "ENSEMBL:ENSMUSG00000059674"
            ],
            "geneid": "239096",
            "name": "cadherin-like 24",
            "organism": {
                "scientific_name": "Mus musculus"
            },
            "symbol": "Cdh24",
            "synonyms": [
                "1700040A22Rik"
            ],
            "title": "Cdh24 (Mus musculus)"
        }
    ]
