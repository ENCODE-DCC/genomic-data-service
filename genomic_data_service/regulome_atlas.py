import pickle
import math
import pyBigWig
from os.path import exists
import logging
from genomic_data_service.constants import GENOME_TO_ALIAS

RESIDENT_REGIONSET_KEY = (
    'resident_regionsets'  # keeps track of what datsets are resident
)
FOR_REGULOME_DB = 'regulomedb'
EVIDENCE_CATEGORIES = [
    'QTL',
    'ChIP',
    'DNase',
    'PWM',
    'Footprint',
    'PWM_matched',
    'Footprint_matched',
]

# when iterating scored snps or bases, chunk calls to index for efficiency
# NOTE: failures seen when chunking is too large
REGDB_SCORE_CHUNK_SIZE = 30000

# RegulomeDB scores for bigWig (bedGraph) are converted to numeric and can be converted back
REGDB_STR_SCORES = [
    '1a',
    '1b',
    '1c',
    '1d',
    '1e',
    '1f',
    '2a',
    '2b',
    '2c',
    '3a',
    '3b',
    '4',
    '5',
    '6',
]
REGDB_NUM_SCORES = [
    1000,
    950,
    900,
    850,
    800,
    750,
    600,
    550,
    500,
    450,
    400,
    300,
    200,
    100,
]

FILE_IC_MATCHED_MAX_HG19_PATH_LOCAL = './ml_models/bigwig_files/IC_matched_max.bw'
FILE_IC_MAX_HG19_PATH_LOCAL = './ml_models/bigwig_files/IC_max.bw'
FILE_IC_MATCHED_MAX_HG19_PATH_REMOTE = 'https://regulome-ml-models.s3.amazonaws.com/bigwig_files/IC_matched_max.bw'
FILE_IC_MAX_HG19_PATH_REMOTE = 'https://regulome-ml-models.s3.amazonaws.com/bigwig_files/IC_max.bw'
FILE_IC_MATCHED_MAX_GRCH38_PATH_LOCAL = './ml_models/bigwig_files/IC_matched_max_GRCh38.bw'
FILE_IC_MAX_GRCH38_PATH_LOCAL = './ml_models/bigwig_files/IC_max_GRCh38.bw'
FILE_IC_MATCHED_MAX_GRCH38_PATH_REMOTE = 'https://regulome-ml-models.s3.amazonaws.com/bigwig_files/IC_matched_max_GRCh38.bw'
FILE_IC_MAX_GRCH38_PATH_REMOTE = 'https://regulome-ml-models.s3.amazonaws.com/bigwig_files/IC_max_GRCh38.bw'

try:
    TRAINED_REG_MODEL = pickle.load(
        open('./ml_models/rf_model1.0.1.sav', 'rb'))
except FileNotFoundError:
    TRAINED_REG_MODEL = None

file_IC_matched_max_hg19_exists = exists(FILE_IC_MATCHED_MAX_HG19_PATH_LOCAL)
file_IC_max_hg19_exists = exists(FILE_IC_MAX_HG19_PATH_LOCAL)
file_IC_matched_max_grch38_exists = exists(
    FILE_IC_MATCHED_MAX_GRCH38_PATH_LOCAL)
file_IC_max_grch38_exists = exists(FILE_IC_MAX_GRCH38_PATH_LOCAL)
try:
    if file_IC_matched_max_hg19_exists:
        IC_MATCHED_MAX_BW_HG19 = pyBigWig.open(
            FILE_IC_MATCHED_MAX_HG19_PATH_LOCAL)
    else:
        IC_MATCHED_MAX_BW_HG19 = pyBigWig.open(
            FILE_IC_MATCHED_MAX_HG19_PATH_REMOTE)
except RuntimeError:
    IC_MATCHED_MAX_BW_HG19 = None

try:
    if file_IC_max_hg19_exists:
        IC_MAX_BW_HG19 = pyBigWig.open(FILE_IC_MAX_HG19_PATH_LOCAL)
    else:
        IC_MAX_BW_HG19 = pyBigWig.open(FILE_IC_MAX_HG19_PATH_REMOTE)
except RuntimeError:
    IC_MAX_BW_HG19 = None

try:
    if file_IC_matched_max_grch38_exists:
        IC_MATCHED_MAX_BW_GRCH38 = pyBigWig.open(
            FILE_IC_MATCHED_MAX_GRCH38_PATH_LOCAL)
    else:
        IC_MATCHED_MAX_BW_GRCH38 = pyBigWig.open(
            FILE_IC_MATCHED_MAX_GRCH38_PATH_REMOTE)
except RuntimeError:
    IC_MATCHED_MAX_BW_GRCH38 = None

try:
    if file_IC_max_grch38_exists:
        IC_MAX_BW_GRCH38 = pyBigWig.open(FILE_IC_MAX_GRCH38_PATH_LOCAL)
    else:
        IC_MAX_BW_GRCH38 = pyBigWig.open(FILE_IC_MAX_GRCH38_PATH_REMOTE)
except RuntimeError:
    IC_MAX_BW_GRCH38 = None

LOCAL_BIGWIGS = {
    'hg19': {
        'IC_matched_max': IC_MATCHED_MAX_BW_HG19,
        'IC_max': IC_MAX_BW_HG19,
    },
    'grch38': {
        'IC_matched_max': IC_MATCHED_MAX_BW_GRCH38,
        'IC_max': IC_MAX_BW_GRCH38,
    },


}

SEARCH_MAX = 9999


class RegulomeAtlas(object):
    def __init__(self, es):
        self.es = es
        self.bigwig_signal_map = LOCAL_BIGWIGS

    def snp_es_index_name(self, assembly):
        return 'snp_' + assembly.lower()

    def find_snp(self, assembly, rsid):
        try:
            res = self.es.get(
                index=self.snp_es_index_name(assembly), doc_type='_all', id=rsid
            )
        except Exception:
            return None

        return res['_source']

    def find_snps(self, assembly, chrom, start, end, max_results=SEARCH_MAX, maf=None):
        range_query = self._range_query(start, end, maf=maf)

        try:
            results = self.es.search(
                index=self.snp_es_index_name(assembly),
                doc_type=chrom,
                _source=True,
                body=range_query,
                size=max_results,
            )
        except Exception:
            return []

        return [hit['_source'] for hit in results['hits']['hits']]

    def find_peaks(
        self, assembly, chrom, start, end, peaks_too=False, max_results=SEARCH_MAX
    ):
        range_query = self._range_query(start, end, max_results=max_results)

        results = self.es.search(
            index=chrom.lower(),
            doc_type=assembly,
            _source=True,
            body=range_query,
            size=max_results,
        )

        return list(results['hits']['hits'])

    def find_peaks_filtered(self, assembly, chrom, start, end, peaks_too=False):
        peaks = self.find_peaks(assembly, chrom, start,
                                end, peaks_too=peaks_too)

        if not peaks:
            return (peaks, None)

        uuids = list(set([peak['_source']['uuid'] for peak in peaks]))
        details = self._resident_details(uuids)
        if not details:
            return ([], details)

        filtered_peaks = []
        for peak in peaks:
            uuid = peak['_source']['uuid']
            if uuid in details:
                peak['resident_detail'] = details[uuid]
                filtered_peaks.append(peak)

        return (filtered_peaks, details)

    def regulome_evidence(self, assembly, datasets, chrom, start, end):
        """Returns evidence for scoring: datasets in a characterized dict"""

        evidence = {}
        targets = {'ChIP': [], 'PWM': [], 'Footprint': []}
        if datasets:
            for dataset in datasets.values():
                character = self._score_category(dataset)
                if character is None:
                    continue
                if character not in evidence:
                    evidence[character] = []
                evidence[character].append(dataset)
                target = dataset.get('target')
                if target and character in ['ChIP', 'PWM', 'Footprint']:
                    if isinstance(target, str):
                        targets[character].append(target)
                    elif isinstance(target, list):  # rare but PWM targets might be list
                        for targ in target:
                            targets[character].append(targ)

        # For each ChIP target, there could be a PWM and/or Footprint to match
        for target in targets['ChIP']:
            if target in targets['PWM']:
                if 'PWM_matched' not in evidence:
                    evidence['PWM_matched'] = []
                evidence['PWM_matched'].append(target)
            if target in targets['Footprint']:
                if 'Footprint_matched' not in evidence:
                    evidence['Footprint_matched'] = []
                evidence['Footprint_matched'].append(target)

        # Get values/signals from bigWig
        assembly = GENOME_TO_ALIAS.get(assembly)
        for k, bw in self.bigwig_signal_map[assembly.lower()].items():
            try:
                values = bw.values(chrom, start, end)
                average = sum(values) / max(len(values), 1)
                evidence[k] = 0.0 if math.isnan(average) else average
            except Exception as e:
                logging.error(
                    'failure to read bigwig file for evidence %s for %s:%s:%s', k, chrom, start, end)
                evidence[k] = 0.0

        return evidence

    @staticmethod
    def _range_query(start, end, maf=None, max_results=SEARCH_MAX):
        # get all peaks that overlap requested point
        # only single point intersection
        # use start not end for 0-base open ended

        query = {'query': {'bool': {'filter': []}}, 'size': max_results}

        if abs(int(end) - int(start)) == 1:
            query_filter = {'term': {'coordinates': start}}
        else:
            query_filter = {
                'range': {
                    'coordinates': {
                        'gte': start,
                        'lt': end,
                        'relation': 'intersects',
                    }
                }
            }

        query['query']['bool']['filter'].append(query_filter)

        if maf is not None:
            query['query']['bool']['filter'].append(
                {'range': {'maf': {'gte': maf}}})

        return query

    def _resident_details(self, uuids, max_results=SEARCH_MAX):
        try:
            id_query = {'query': {'ids': {'values': uuids}}}
            res = self.es.search(
                index=RESIDENT_REGIONSET_KEY,
                body=id_query,
                doc_type=[FOR_REGULOME_DB],
                size=max_results,
            )
        except Exception:
            return None

        details = {}

        hits = res.get('hits', {}).get('hits', [])
        for hit in hits:
            details[hit['_source']['uuid']] = hit['_source']

        return details

    @staticmethod
    def _peak_uuids_in_overlap(peaks, chrom, start, end=None):
        """private: returns set of only the uuids for peaks that overlap a given location"""
        if end is None:
            end = start

        overlap = set()
        for peak in peaks:
            if (
                chrom == peak['_index']
                and start <= peak['_source']['coordinates']['lt']
                and end >= peak['_source']['coordinates']['gte']
            ):
                overlap.add(peak['_source']['uuid'])

        return overlap

    @staticmethod
    def _filter_details(details, uuids=None, peaks=None):
        """private: returns only the details that match the uuids"""
        if uuids is None:
            assert peaks is not None
            uuids = list(set([peak['_source']['uuid'] for peak in peaks]))
        filtered = {}
        for uuid in uuids:
            if uuid in details:  # region peaks may not be in regulome only details
                filtered[uuid] = details[uuid]
        return filtered

    @staticmethod
    def details_breakdown(details, uuids=None):
        """Return dataset and file dicts from resident details dicts."""
        if not details:
            return (None, None)
        file_dets = {}
        dataset_dets = {}
        if uuids is None:
            uuids = details.keys()
        for uuid in uuids:
            if uuid not in details:
                continue
            afile = details[uuid]['file']
            file_dets[afile['@id']] = afile
            dataset = details[uuid]['dataset']
            dataset_dets[dataset['@id']] = dataset
        return (dataset_dets, file_dets)

    @staticmethod
    def evidence_categories():
        return EVIDENCE_CATEGORIES

    @staticmethod
    def _score_category(dataset):
        """private: returns one of the categories of evidence that are needed for scoring."""
        # score categories are slighly different from regulome categories
        collection_type = dataset.get(
            'collection_type', ''
        ).lower()  # resident_regionset dataset
        if collection_type in ['chip-seq', 'binding sites']:
            return 'ChIP'
        if collection_type == 'dnase-seq':
            return 'DNase'
        if collection_type == 'pwms':
            return 'PWM'
        if collection_type == 'footprints':
            return 'Footprint'
        if collection_type in ['eqtls', 'dsqtls', 'curated snvs']:
            return 'QTL'
        return None

    def _regulome_category(self, score_category=None, dataset=None):
        """private: returns one of the categories used to present evidence in a bed file."""
        # regulome category 'Motifs' contains score categories 'PWM' and 'Footprint'
        if score_category is None:
            if dataset is None:
                return '???'
            score_category = self._score_category(dataset)
        if score_category == 'ChIP':
            return 'Protein_Binding'
        if score_category == 'DNase':
            return 'Chromatin_Structure'
        if score_category in ['PWM', 'Footprint']:
            return 'Motifs'
        if score_category == 'QTL':
            return 'Single_Nucleotides'
        return '???'

    def _write_a_brief(self, category, snp_evidence):
        """private: given evidence for a category make a string that summarizes it"""
        snp_evidence_category = snp_evidence[category]

        # What do we want the brief to look like?
        # Regulome: Chromatin_Structure|DNase-seq|Chorion|,
        #           Chromatin_Structure|DNase-seq|Adultcd4th1|,
        #           Protein_Binding|ChIP-seq|E2F1|MCF-7|, ...
        # Us: Chromatin_Structure:DNase-seq:|ENCSR...|Chorion|,|ENCSR...|Adultcd4th1| (tab)
        #           Protein_Binding/ChIP-seq:|ENCSR...|E2F1|MCF-7|,|ENCSR...|SP4|H1-hESC|
        brief = ''
        cur_score_category = ''
        cur_regdb_category = ''
        for dataset in snp_evidence_category:
            new_score_category = self._score_category(dataset)
            if cur_score_category != new_score_category:
                cur_score_category = new_score_category
                new_regdb_category = self._regulome_category(
                    cur_score_category)
                if cur_regdb_category != new_regdb_category:
                    cur_regdb_category = new_regdb_category
                    if brief != '':  # 'PWM' and 'Footprint' are both 'Motif'
                        brief += ';'
                    brief += '%s:' % cur_regdb_category
                brief += '%s:|' % cur_score_category
            try:
                brief += (
                    dataset.get('@id', '').split('/')[-2] + '|'
                )  # accession is buried in @id
            except Exception:
                brief += '|'
            target = dataset.get('target')
            if target:
                if isinstance(target, list):
                    target = '/'.join(target)
                brief += target.replace(' ', '') + '|'
            biosample = dataset.get(
                'biosample_term_name', dataset.get('biosample_summary')
            )
            if biosample:
                brief += biosample.replace(' ', '') + '|'
            brief += ','
        return brief[:-1]  # remove last comma

    def make_a_case(self, snp):
        """Convert evidence json to list of evidence strings for bed batch downloads."""
        case = {}
        if 'evidence' in snp:
            for category in snp['evidence'].keys():
                if category.endswith('_matched'):
                    case[category] = ','.join(snp['evidence'][category])
                else:
                    case[category] = self._write_a_brief(
                        category, snp['evidence'])
        return case

    @staticmethod
    def _score(characterization):
        """private: returns regulome score from characterization set"""
        # Predict as probability of being a regulatory SNP from prediction
        binary_keys = [
            'ChIP',
            'DNase',
            'PWM',
            'Footprint',
            'QTL',
            'PWM_matched',
            'Footprint_matched',
        ]
        query = [int(k in characterization) for k in binary_keys]
        numeric_keys = ['IC_max', 'IC_matched_max']
        query += [characterization[k] for k in numeric_keys]
        # The TRAINED_REG_MODEL is a `sklearn.ensemble.forest.RandomForestClassifier`
        # https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
        # In general, the input of the `predict_proba` method is a matrix of
        # shape = [n_variants, n_features]. There are two classes for variant
        # in RegulomeDB, being allele-specific TF binding or not. So the output
        # is an numpy array of shape = [n_samples, 2]. Here, we only do one
        # variant at a time. So `query` is a list of lists with
        # shape = [1, n_features] and the output of
        # `TRAINED_REG_MODEL.predict_proba([query])` is numpy array of
        # shape = [1, 2]. Specifically, the second column is the probability we
        # would like to output. So `[:, 1][0]` will be the desired score.
        probability = str(
            round(TRAINED_REG_MODEL.predict_proba([query])[:, 1][0], 5))
        ranking = '7'
        if 'QTL' in characterization:
            if 'ChIP' in characterization:
                if 'DNase' in characterization:
                    if (
                        'PWM_matched' in characterization
                        and 'Footprint_matched' in characterization
                    ):
                        ranking = '1a'
                    elif 'PWM' in characterization and 'Footprint' in characterization:
                        ranking = '1b'
                    elif 'PWM_matched' in characterization:
                        ranking = '1c'
                    elif 'PWM' in characterization:
                        ranking = '1d'
                    else:
                        ranking = '1f'
                elif 'PWM_matched' in characterization:
                    ranking = '1e'
                else:
                    ranking = '1f'
            elif 'DNase' in characterization:
                ranking = '1f'
            elif 'PWM' in characterization or 'Footprint' in characterization:
                ranking = '6'
        elif 'ChIP' in characterization:
            if 'DNase' in characterization:
                if (
                    'PWM_matched' in characterization
                    and 'Footprint_matched' in characterization
                ):
                    ranking = '2a'
                elif 'PWM' in characterization and 'Footprint' in characterization:
                    ranking = '2b'
                elif 'PWM_matched' in characterization:
                    ranking = '2c'
                elif 'PWM' in characterization:
                    ranking = '3a'
                else:
                    ranking = '4'
            elif 'PWM_matched' in characterization:
                ranking = '3b'
            else:
                ranking = '5'
        elif 'DNase' in characterization:
            ranking = '5'
        elif 'PWM' in characterization or 'Footprint' in characterization:
            ranking = '6'
        return {'probability': probability, 'ranking': ranking}

    def regulome_score(self, datasets, evidence):
        """Calculate RegulomeDB score based upon hits and voodoo"""
        if not evidence:
            return None
        return self._score(evidence)

    @staticmethod
    def _snp_window(snps, window, center_pos=None):
        """Reduce a list of snps to a set number of snps centered around position"""
        if len(snps) <= window:
            return snps

        snps = sorted(snps, key=lambda s: s['coordinates']['gte'])
        ix = 0
        for snp in snps:
            if snp['coordinates']['gte'] >= center_pos:
                break
            ix += 1

        first_ix = int(ix - (window / 2))
        if first_ix > 0:
            snps = snps[first_ix:]
        return snps[:window]

    def _scored_snps(self, assembly, chrom, start, end, window=-1, center_pos=None):
        """For a region, yields all SNPs with scores"""
        snps = self.find_snps(assembly, chrom, start, end)
        if not snps:
            return
        if window > 0:
            snps = self._snp_window(snps, window, center_pos)

        # SNPs must be in location order!
        start = snps[0]['coordinates']['gte']
        end = snps[-1]['coordinates']['lt']  # MUST do SLOW peaks_too
        (peaks, details) = self.find_peaks_filtered(
            assembly, chrom, start, end, peaks_too=True
        )
        if not peaks or not details:
            for snp in snps:
                snp['score'] = None
                yield snp
                return

        last_uuids = {}
        for snp in snps:
            snp['score'] = None  # default
            snp['assembly'] = assembly
            snp_uuids = self._peak_uuids_in_overlap(
                peaks, snp['chrom'], snp['coordinates']['gte']
            )
            if snp_uuids:
                # Otherwise datasets hits would be the same
                if snp_uuids != last_uuids:
                    last_uuids = snp_uuids
                    snp_details = self._filter_details(
                        details, uuids=list(snp_uuids))
                    if snp_details:
                        (snp_datasets, _snp_files) = self.details_breakdown(
                            snp_details)
                    else:
                        snp_datasets = {}
                # Regulome evidence now includes signals from bigWig.
                # Better to recalculate for every new locations.
                if snp_datasets:
                    snp_evidence = self.regulome_evidence(
                        assembly,
                        snp_datasets,
                        snp['chrom'],
                        snp['coordinates']['gte'],
                        snp['coordinates']['lt'],
                    )
                    if snp_evidence:
                        snp['score'] = self.regulome_score(
                            snp_datasets, snp_evidence)
                        snp['evidence'] = snp_evidence
                        yield snp
                        continue
            # if we are here this snp had no score
            yield snp

    def _scored_regions(self, assembly, chrom, start, end):
        """For a region, yields sub-regions (start, end, score) of contiguous numeric score > 0"""
        (peaks, details) = self.find_peaks_filtered(
            assembly, chrom, start, end, peaks_too=True
        )
        if not peaks or not details:
            return

        last_uuids = set()
        region_start = 0
        region_end = 0
        region_score = 0
        num_score = 0
        for base in range(start, end):
            base_uuids = self._peak_uuids_in_overlap(peaks, chrom, base)
            if base_uuids:
                # For now we will combine nucleotides as long as peaks are the
                # same. But keep in mind regulome evidence now includes signals
                # from bigWigs, which are very likely different from nucleotide
                # to nucleotide.
                if base_uuids == last_uuids:
                    region_end = base  # extend region
                    continue
                else:
                    last_uuids = base_uuids
                    base_details = self._filter_details(
                        details, uuids=list(base_uuids))
                    if base_details:
                        (base_datasets, _base_files) = self.details_breakdown(
                            base_details
                        )
                        if base_datasets:
                            base_evidence = self.regulome_evidence(
                                assembly, base_datasets, chrom, start, end
                            )
                            if base_evidence:
                                score = self.regulome_score(
                                    base_datasets, base_evidence
                                ).get('ranking', '')
                                if score:
                                    num_score = self.numeric_score(score)
                                    if num_score == region_score:
                                        region_end = base
                                        continue
                                    if region_score > 0:  # end previous region?
                                        yield (region_start, region_end, region_score)
                                    # start new region
                                    region_score = num_score
                                    region_start = base
                                    region_end = base
                                    continue
            # if we are here this base had no score
            if region_score > 0:  # end previous region?
                yield (region_start, region_end, region_score)
                region_score = 0
                last_uuids = base_uuids  # zero score so don't try these uuids again!

        if region_score > 0:  # end previous region?
            yield (region_start, region_end, region_score)

    def nearby_snps(
        self, assembly, chrom, pos, rsid=None, window=1600, max_snps=10, scores=False
    ):
        """Return SNPs nearby to the chosen SNP."""
        if rsid:
            max_snps += 1

        range_start = int(pos - (window / 2))
        range_end = int(pos + (window / 2))
        if range_start < 0:
            range_end += 0 - range_start
            range_start = 0

        if scores:
            return self._scored_snps(assembly, chrom, range_start, range_end)
        else:
            snps = self.find_snps(assembly, chrom, range_start, range_end)
            return self._snp_window(snps, max_snps, pos)

    def iter_scored_snps(self, assembly, chrom, start, end, base_level=False):
        """For a region, iteratively yields all SNPs with scores."""
        if end < start:
            return
        chunk_size = REGDB_SCORE_CHUNK_SIZE
        chunk_start = start
        while chunk_start <= end:
            chunk_end = chunk_start + chunk_size
            if chunk_end > end:
                chunk_end = end
            yield from self._scored_snps(assembly, chrom, chunk_start, chunk_end)
            chunk_start += chunk_size

    def iter_scored_signal(self, assembly, chrom, start, end):
        """For a region, iteratively yields all bedGraph styled regions
        of contiguous numeric score."""
        if end < start:
            return
        chunk_size = REGDB_SCORE_CHUNK_SIZE
        chunk_start = start
        while chunk_start <= end:
            chunk_end = chunk_start + chunk_size
            if chunk_end > end:
                chunk_end = end
            yield from self._scored_regions(assembly, chrom, chunk_start, chunk_end)
            chunk_start += chunk_size

    def live_score(self, assembly, chrom, pos):
        """Returns score knowing single position and nothing more."""
        (peaks, details) = self.find_peaks_filtered(assembly, chrom, pos, pos)
        if not peaks or not details:
            return None
        (datasets, _files) = self.details_breakdown(details)
        evidence = self.regulome_evidence(
            assembly, datasets, chrom, pos, pos + 1)
        return self.regulome_score(datasets, evidence)

    @staticmethod
    def numeric_score(alpha_score):
        """converst str score to numeric representation (for bedGraph)"""
        try:
            return REGDB_NUM_SCORES[REGDB_STR_SCORES.index(alpha_score)]
        except Exception:
            return 0

    @staticmethod
    def str_score(int_score):
        """converst numeric representation of score to standard string score"""
        try:
            return REGDB_STR_SCORES[REGDB_NUM_SCORES.index(int_score)]
        except Exception:
            return ''
