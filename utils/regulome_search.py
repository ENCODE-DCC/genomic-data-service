import argparse
import json
from multiprocessing import Pool
import sys
from tempfile import TemporaryFile
from elasticsearch import Elasticsearch
from genomic_data_service import app
from genomic_data_service.constants import GENOME_TO_ALIAS
from genomic_data_service.rsid_coordinates_resolver import (
    get_coordinates,
    region_get_hits,
    evidence_to_features
)
from genomic_data_service.regulome_atlas import RegulomeAtlas


class RegulomeApp:
    """Start an independent app to do regulome search.
    """
    motif_columns = (
        '{chrom}\t'
        '{start}\t'
        '{end}\t'
        '{motif_name}\t'
        '{strand}\t'
        '{hit_motif_start}\t'
        '{hit_motif_end}\t'
        '{query}\t'
        '{query_start}\t'
        '{query_end}'
    )

    def __init__(
        self,
        assembly,
        return_peaks,
        matched_pwm_peak_bed_only,
        search_snps_in_region,
        maf,
    ):
        self.assembly = assembly
        self.return_peaks = return_peaks
        self.matched_pwm_peak_bed_only = matched_pwm_peak_bed_only
        self.search_snps_in_region = search_snps_in_region
        self.maf = maf

    @property
    def atlas(self):
        regulome_es = Elasticsearch(
            port=app.config['REGULOME_ES_PORT'], hosts=app.config['REGULOME_ES_HOSTS']
        )
        self._atlas = RegulomeAtlas(regulome_es)
        return self._atlas

    def search(self, normalized_query):
        result = json.loads(normalized_query)
        if 'chrom' not in result:
            return 1, result.get(
                'notes',
                'Invalid input: {}'.format(result.get('query', 'None'))
            )
        chrom = result['chrom']
        start = result['start']
        end = result['end']

        all_hits = region_get_hits(
            self.atlas,
            self.assembly,
            chrom,
            start,
            end,
            peaks_too=self.return_peaks or self.matched_pwm_peak_bed_only
        )
        datasets = all_hits.get('datasets', [])

        try:
            evidence = self.atlas.regulome_evidence(
                self.assembly, datasets, chrom, int(start), int(end)
            )
            if not self.matched_pwm_peak_bed_only:
                result['score'] = self.atlas.regulome_score(
                    datasets, evidence
                )
                result['features'] = evidence_to_features(evidence)
        except Exception:
            return 1, 'Regulome search failed on {}:{}-{}'.format(
                chrom, start, end
            )

        if self.matched_pwm_peak_bed_only:
            if not evidence.get('PWM_matched', []):
                return 0, ''
            matched_pwm_dict = {}
            for motif in evidence.get('PWM', []):
                if set(evidence['PWM_matched']) & set(motif.get('target', [])):
                    matched_pwm_dict[motif['@id']] = [
                        alias.split(sep=':', maxsplit=1)[1]
                        for doc in motif['documents']
                        for alias in doc['aliases']
                    ]
            motif_peaks = []
            for peak in all_hits.get('peaks', []):
                dataset = peak['resident_detail']['dataset']
                if dataset['@id'] not in matched_pwm_dict:
                    continue
                motif_peak = {
                    'chrom': peak['_index'],
                    'start': peak['_source']['coordinates']['gte'],
                    'end': peak['_source']['coordinates']['lt'],
                    'motif_name': ','.join(matched_pwm_dict[dataset['@id']]),
                    'strand': peak['_source'].get('strand', '.'),
                    'query': result['query'],
                    'query_start': start,
                    'query_end': end,
                }
                if motif_peak['strand'] == '-':
                    motif_peak['hit_motif_start'] = motif_peak['end'] - end
                    motif_peak['hit_motif_end'] = motif_peak['end'] - start
                else:
                    motif_peak['hit_motif_start'] = start - motif_peak['start']
                    motif_peak['hit_motif_end'] = end - motif_peak['start']
                motif_peaks.append(motif_peak)
            motif_peaks = [self.motif_columns.format(
                **motif_peak) for motif_peak in motif_peaks]
            motif_peaks_table = '\n'.join(motif_peaks)
            return 0, motif_peaks_table
        if self.return_peaks:
            result['peaks'] = []
            for peak in all_hits.get('peaks', []):
                method = peak['resident_detail']['dataset']['collection_type']
                if method in [
                    'FAIRE-seq',
                    'chromatin state',
                    'binding sites',
                    'curated SNVs'
                ]:
                    continue
                peak_info = {
                    'method': method,
                }
                if method in ['ChIP-seq', 'Footprints', 'PWMs']:
                    peak_info['targets'] = peak[
                        'resident_detail'
                    ]['dataset'].get('target', [])
                if method == 'PWMs':
                    peak_info.update({
                        'chrom': peak['_index'],
                        'start': peak['_source']['coordinates']['gte'],
                        'end': peak['_source']['coordinates']['lt'],
                        'strand': peak['_source'].get('strand'),
                        'document_aliases': [
                            alias
                            for doc in peak['resident_detail']['dataset'][
                                'documents'
                            ]
                            for alias in doc['aliases']
                        ],
                    })
                else:
                    peak_info['biosample_term_name'] = peak[
                        'resident_detail'
                    ]['dataset']['biosample_ontology']['term_name']
                result['peaks'].append(peak_info)
        return 0, json.dumps(result)

    def normalize_query(self, region_query):
        region_query = region_query.strip()
        try:
            chrom, start, end = get_coordinates(
                region_query, self.assembly, self.atlas
            )
        except ValueError:
            return [
                json.dumps(
                    {
                        'query': region_query,
                        'notes': 'Failed to parse query into valid region(s).'
                    }
                )
            ]
        if not self.search_snps_in_region:
            return [
                json.dumps(
                    {
                        'query': region_query,
                        'chrom': chrom,
                        'start': start,
                        'end': end,
                    }
                )
            ]
        try:
            snps = self.atlas.find_snps(
                GENOME_TO_ALIAS.get(self.assembly, self.assembly),
                chrom,
                start,
                end,
                maf=self.maf,
            )
        except Exception:
            snps = []
        if not snps:
            if end - start > 1:
                return [
                    json.dumps(
                        {
                            'query': region_query,
                            'notes': 'Query region is not single nt (SNP) and no RefSNPs is found within the query region.'
                        }
                    )
                ]
            return [
                json.dumps(
                    {
                        'query': region_query,
                        'chrom': chrom,
                        'start': start,
                        'end': end,
                        'ref_snp': {},
                    }
                )
            ]
        return [
            json.dumps(
                {
                    'query': region_query,
                    'chrom': snp['chrom'],
                    'start': snp['coordinates']['gte'],
                    'end': snp['coordinates']['lt'],
                    'ref_snp': {
                        'rsid': snp['rsid'],
                        'ref_alleles': sorted(snp.get('ref_allele_freq', [])),
                        'alt_alleles': sorted(snp.get('alt_allele_freq', [])),
                    },
                }
            )
            for snp in snps
        ]


def main():
    parser = argparse.ArgumentParser(
        description='Regulome search for one or more variations.'
    )
    # sudo -u encoded bin/regulome-search -s rs3768324 chr1:39492462-39492463
    parser.add_argument(
        '--assembly',
        help="Select 'GRCh37' or 'GRCh38'. Default: 'GRCh37'.",
        choices=['GRCh37', 'GRCh38'],
        default='GRCh37'
    )
    parser.add_argument(
        '--peaks',
        help='Return peaks. By default, only scores will be return.',
        action='store_true',
    )
    parser.add_argument(
        '--matched-pwm-peak-only',
        help='Return motif peak details in BED format.',
        action='store_true',
    )
    parser.add_argument(
        '-p', '--processes',
        type=int,
        default=1,
        help='Number of process run in parallel.'
    )
    parser.add_argument(
        '--search-snps-in-region',
        action='store_true',
        help='Treat each query region as one single region instead of looking'
        ' at RefSNPs in it.'
    )

    def maf_type(s):
        if s.lower() == 'none':
            return None
        try:
            return float(s)
        except ValueError:
            raise argparse.ArgumentTypeError(
                '{} is not a float number or "None".'.format(s)
            )

    parser.add_argument(
        '--maf',
        type=maf_type,
        default=0.01,
        help='Minor allele frequency cut off. Only RefSNPs more frequent than'
        ' this cut off will be returned. It can be a float number or None if'
        ' all RefSNPs should be returned. Default is 0.01 (1%%).'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-s', '--variants',
        nargs='+',
        help='One or more variants. Two formats can be accepted: 1) RefSNP ID '
        'such as rs3768324; 2) Genome coordinates in the format like: '
        'chr1:39492462-39492463.'
    )
    group.add_argument(
        '-f', '--file-input',
        help='One file with variants to be searched. Each row will be '
        'interpreted as one region. It can be a dbSNP ID, a BED format region '
        'or a region like chr1:39492462-39492463.'
    )
    args = parser.parse_args()

    if args.file_input:
        query_count = 0
        with open(args.file_input) as f:
            for query_count, _ in enumerate(f, 1):
                pass
        query_stream = open(args.file_input)
    elif args.variants:
        query_count = len(args.variants)
        query_stream = TemporaryFile(mode='w+')
        for query_region in args.variants:
            query_stream.write('{}\n'.format(query_region))
        query_stream.seek(0)
    chunksize = query_count // args.processes + \
        (query_count % args.processes > 0)

    print(
        'Found {} queries and converting them to potential {}...'.format(
            query_count,
            'variants' if args.search_snps_in_region else 'regions',
        ),
        file=sys.stderr
    )
    variant_stream = TemporaryFile(mode='w+')
    variant_count = 0
    with query_stream as queries:
        with Pool(args.processes) as p:
            for variants in p.imap(
                RegulomeApp(
                    args.assembly,
                    args.peaks,
                    args.matched_pwm_peak_only,
                    args.search_snps_in_region,
                    args.maf,
                ).normalize_query,
                queries,
                chunksize
            ):
                for variant in variants:
                    variant_count += 1
                    variant_stream.write('{}\n'.format(variant))
    variant_stream.seek(0)
    variant_chunksize = variant_count // args.processes + (
        variant_count % args.processes > 0
    )

    print(
        'Querying {} {} using {} processes with chunksize {}...'.format(
            variant_count,
            'variants' if args.search_snps_in_region else 'regions',
            args.processes,
            variant_chunksize,
        ),
        file=sys.stderr
    )
    success_count = 0
    failure_count = 0
    with variant_stream as variants:
        with Pool(args.processes) as p:
            for status, res in p.imap(
                RegulomeApp(
                    args.assembly,
                    args.peaks,
                    args.matched_pwm_peak_only,
                    args.search_snps_in_region,
                    args.maf,
                ).search,
                variants,
                variant_chunksize
            ):
                if status == 0:
                    print(res)
                    success_count += 1
                else:
                    print(res, file=sys.stderr)
                    failure_count += 1
    print(
        'Succeeded {}; Failed: {}'.format(success_count, failure_count),
        file=sys.stderr
    )


if __name__ == '__main__':
    main()
