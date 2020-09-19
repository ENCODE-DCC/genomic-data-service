import datetime
import urllib3
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError, HTTPError
import io
import gzip
import csv
import logging
import json
import requests
import os
from pkg_resources import resource_filename
from pyramid.settings import asbool
from pyramid.view import view_config
from shutil import copyfileobj
from elasticsearch.exceptions import (
    NotFoundError
)
from elasticsearch.helpers import (
    bulk
)
from sqlalchemy.exc import StatementError
from snovault.elasticsearch.indexer import (
    Indexer
)
from snovault.elasticsearch.indexer_state import (
    SEARCH_MAX,
    IndexerState
)

from snovault.elasticsearch.interfaces import (
    ELASTIC_SEARCH,
    SNP_SEARCH_ES,
    INDEXER,
)

log = logging.getLogger(__name__)

# ##################################
# Region indexer 2.0
# What it does:
# 1) get list of uuids of primary indexer and filter down to datasets covered
# 2) walk through uuid list querying encoded for each doc[embedded]
#    3) Walk through embedded files
#       4) If file passes required tests (e.g. bed, released, ...)
#          AND not in regions_es, put in regions_es
#       5) If file does not pass tests
#          AND     IN regions_es, remove from regions_es
# TODO:
# Add score to snp indexing (takes a LONG time to calculate them all)
# Add nearby snps (with scores) to regulome-search, and means to select them!
#     only after scores are in index
# Update resident doc, even when file is already resident.
# ##################################
REGION_INDEXER_SHARDS = 2
RETRYABLE_STATUS = (500, 502, 504,)


# TEMPORARY: limit SNPs to major chroms
SUPPORTED_CHROMOSOMES = [
    'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9',
    'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17',
    'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrX', 'chrY'
]  # chroms are lower case

ALLOWED_FILE_FORMATS = ['bed']
RESIDENT_REGIONSET_KEY = 'resident_regionsets'  # keeps track of what datsets are resident
FOR_REGULOME_DB = 'regulomedb'

REGULOME_SUPPORTED_ASSEMBLIES = ['hg19', 'GRCh38']
REGULOME_ALLOWED_STATUSES = ['released', 'archived']  # no 'in progress' permission!
REGULOME_DATASET_TYPES = ['Experiment', 'Annotation', 'Reference']
REGULOME_COLLECTION_TYPES = ['assay_term_name', 'annotation_type', 'reference_type']
# NOTE: regDB requirements keyed on "collection_type": assay_term_name or else annotation_type
REGULOME_REGION_REQUIREMENTS = {
    'ChIP-seq': {
        'output_type': ['optimal idr thresholded peaks'],
        'file_format': ['bed']
    },
    'binding sites': {
        'output_type': ['curated binding sites'],
        'file_format': ['bed']
    },
    'DNase-seq': {
        'output_type': ['peaks'],
        'file_type': ['bed narrowPeak'],
        'file_format': ['bed']
    },
    'FAIRE-seq': {
        'file_type': ['bed narrowPeak'],
        'file_format': ['bed']
    },
    'chromatin state': {
        'file_format': ['bed']
    },
    'PWMs': {
        'output_type': ['PWMs'],
        'file_format': ['bed']
    },
    'Footprints': {
        'output_type': ['Footprints'],
        'file_format': ['bed']
    },
    'eQTLs': {
        'file_format': ['bed']
    },
    'dsQTLs': {
        'file_format': ['bed']
    },
    'curated SNVs': {
        'output_type': ['curated SNVs'],
        'file_format': ['bed']
    },
    'index': {  # TODO: reference of variant calls doesn't yet exist.  'index' is temporary
        'output_type': ['variant calls'],
        'file_format': ['bed']
    }
}
# Columns (0-based) for value and strand to be indexed
REGULOME_VALUE_STRAND_COL = {
    'ChIP-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'DNase-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'FAIRE-seq': {
        'strand_col': 5,
        'value_col': 6
    },
    'chromatin state': {
        'value_col': 3
    },
    'eQTLs': {
        'value_col': 5
    },
    'Footprints': {
        'strand_col': 5,
    },
    'PWMs': {
        'strand_col': 4,
    },
}
# Less than ideal way to recognize the SNP files by submitted_file_name
# SNP_DATASET_UUID = 'ff8dff4e-1de5-446b-8a13-bb6243bc64aa'  # works on demo, but...
SNP_INDEX_PREFIX = 'snp_'

# If files are too large then they will be copied locally and read
MAX_IN_MEMORY_FILE_SIZE = (700 * 1024 * 1024)  # most files will be below this and index faster
TEMPORARY_REGIONS_FILE = '/tmp/region_temp.bed.gz'

# Max number of SNP docs hold in memory before putting into the index
MAX_SNP_BULK = 3e6


def includeme(config):
    config.add_route('index_region', '/index_region')
    config.scan(__name__)
    config.add_route('_regionindexer_state', '/_regionindexer_state')
    registry = config.registry
    is_region_indexer = registry.settings.get('regionindexer')
    if is_region_indexer:
        registry['region'+INDEXER] = RegionIndexer(registry)

def tsvreader(file):
    reader = csv.reader(file, delimiter='\t')
    for row in reader:
        yield row

# Mapping should be generated dynamically for each assembly type


# Region mapping: index: chr*, doc_type: assembly, _id=uuid
def get_chrom_index_mapping(assembly_name='hg19'):
    return {
        assembly_name: {
            '_source': {
                'enabled': True
            },
            # could eventually index biological metadata here
            'properties': {
                'uuid': {
                    'type': 'keyword'  # WARNING: to add local files this must be 'type': 'string'
                },
                'coordinates': {
                    'type': 'integer_range'
                },
                'strand': {
                    'type': 'string'  # + - .
                },
                'value': {
                    'type': 'string'  # some signal value
                },
            }
        }
    }


# Files are also put in the resident: index: RESIDENT_REGIONSET_KEY, doc_type: use_type, _id=uuid
def get_resident_mapping(use_type=FOR_REGULOME_DB):
    return {use_type: {"enabled": False}}
    # True map: IF we ever want to query by anything other than uuid...
    # return {
    #     use_type: {
    #         '_all':    {'enabled': False},
    #         '_source': {'enabled': True},
    #         'properties': {
    #             'uuid':   {'type': 'keyword'},  # same as _id and file['uuid']
    #             'uses':   {'type': 'keyword'},  # e.g FOR_REGULOME_DB
    #             'chroms': {'type': 'keyword'},  # Used to remove from 'chr*' indices
    #             'snps':   {'type': 'boolean'},  # If present, then this is a file of SNPs
    #             'index':  {'type': 'keyword'},  # If present, the 1 index for this 1 SNP file
    #             'file': {
    #                 'properties': {
    #                     'uuid':     {'type': 'keyword'},  # Yes, redundant
    #                     '@id':      {'type': 'keyword'},
    #                     'assembly': {'type': 'keyword'},
    #                 }
    #             },
    #             'dataset': {
    #                 'properties': {
    #                     'uuid':            {'type': 'keyword'},
    #                     '@id':             {'type': 'keyword'},
    #                     'assay_term_name': {'type': 'keyword'},  # \
    #                     'annotation_type': {'type': 'keyword'},  # - only one will appear
    #                     'reference_type':  {'type': 'keyword'},  # /
    #                     'collection_type': {'type': 'keyword'},  # assay or else annotation
    #                     'target':          {'type': 'keyword'},  # could be array (PWM targets)
    #                     'dataset_type':    {'type': 'keyword'}   # 1st of *_PRIORITIZED_TYPES
    #                 }
    #             }
    #         }
    #     }
    # }


# SNP mapping index: snp141_hg19, doc_type: chr*, _id=rsid
# this might need strand too for visualization
def get_snp_index_mapping(chrom='chr1'):
    return {
        chrom: {
            '_all': {
                'enabled': False
            },
            '_source': {
                'enabled': True
            },
            'properties': {
                'rsid': {
                    'type': 'keyword'
                },
                'chrom': {
                    'type': 'keyword'
                },
                'coordinates': {
                    'type': 'integer_range'
                },
                'maf': {
                    'type': 'float',
                },
                'ref_allele_freq': {
                    'enabled': False,
                },
                'alt_allele_freq': {
                    'enabled': False,
                },
            }
        }
    }
# This results in too much stress on elasticsearch: it crashes doring indexing of 60M rsids
#                'suggest' : {
#                    'type' : 'completion'
#                },


def snp_index_key(assembly):
    return SNP_INDEX_PREFIX + assembly.lower()


def index_settings():
    return {
        'index': {
            'number_of_shards': REGION_INDEXER_SHARDS,
            'max_result_window': SEARCH_MAX
        }
    }


def regulome_regionable_datasets(request):
    type_query = '&'.join(
        'type={}'.format(typ) for typ in REGULOME_DATASET_TYPES
    )
    status_query = '&'.join(
        'status={}'.format(status) for status in REGULOME_ALLOWED_STATUSES
    )
    results = request.embed(
        '/search/?{}&{}&files=*&field=uuid&limit=all'.format(
            type_query, status_query
        )
    )['@graph']
    return [result['uuid'] for result in results]


def regulome_collection_type(dataset):
    for prop in REGULOME_COLLECTION_TYPES:
        if prop in dataset:
            return dataset[prop]
    return None


class RemoteReader(object):
    # Tools for reading remote files

    def __init__(self):
        self.temp_file = TEMPORARY_REGIONS_FILE
        self.max_memory = MAX_IN_MEMORY_FILE_SIZE

    def readable_file(self, request, afile):
        '''returns either an in memory file or a temp file'''

        # Special case local instance so that tests can work...
        if asbool(request.registry.settings.get('testing')):
            filedir = resource_filename('encoded', 'tests/data/files/')
            filename = os.path.basename(afile['href'])
            file_to_read = os.path.join(filedir, filename)
            if not os.path.isfile(file_to_read):
                log.warn("File (%s or %s) not found" % (
                    afile.get('accession', id), afile['href']
                ))
                return False
            return file_to_read

        href = request.host_url + afile['href']
        # TODO: support for remote access for big files (could do bam and vcf as well)
        # if afile.get('file_format') in ['bigBed', 'bigWig']:
        #     return href
        # assert(afile.get('file_format') == 'bed')

        # Note: this reads the file into an in-memory byte stream.  If files get too large,
        # We could replace this with writing a temp file, then reading it via gzip and tsvreader.
        urllib3.disable_warnings()
        http = urllib3.PoolManager()

        # use afile.get(file_size) to decide between in mem file or temp file
        file_to_read = None
        if afile.get('file_size', 0) > self.max_memory:
            with http.request('GET', href, preload_content=False) \
                    as r, open(self.temp_file, 'wb') as out_file:
                copyfileobj(r, out_file)
            file_to_read = self.temp_file
            log.warn('Wrote %s to %s', href, file_to_read)
        else:
            try:
                r = http.request('GET', href, retries=Retry(status_forcelist=RETRYABLE_STATUS,
                                                            backoff_factor=1))
            except MaxRetryError as e:
                log.warn(e.reason)
                log.warn("File (%s or %s) not found" % (afile['@id'], href))
                raise
            else:
                if r.status != 200:
                    http_error_msg = "STATUS %s: File (%s or %s) not found" % (r.status, afile['@id'], href)
                    log.warn(http_error_msg)
                    raise HTTPError(http_error_msg)
            file_in_mem = io.BytesIO()
            file_in_mem.write(r.data)
            file_in_mem.seek(0)
            file_to_read = file_in_mem
        r.release_conn()

        return file_to_read

    @staticmethod
    def tsv(file_handle):
        reader = csv.reader(file_handle, delimiter='\t')
        for row in reader:
            yield row

    @staticmethod
    def region(row, value_col=None, strand_col=None):
        '''Read a region from an in memory row and returns chrom and document to index.
           Extend this to get store and strand properties, although the bed files vary by type
        '''
        chrom, start, end = row[0], int(row[1]), int(row[2])
        doc = {
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }  # Stored as BED 0-based half open
        if value_col and value_col < len(row):
            doc['value'] = row[value_col]
        if strand_col:
            # Some PWMs annotation doesn't have strand info
            if strand_col < len(row) and row[strand_col] in ['.', '+', '-']:
                doc['strand'] = row[strand_col]
            # Temporary hack for Footprint data
            elif (
                strand_col - 1 < len(row)
                and row[strand_col - 1] in ['.', '+', '-']
            ):
                doc['strand'] = row[strand_col - 1]
            else:
                doc['strand'] = '.'
        return (chrom, doc)

    @staticmethod
    def snp(row):
        '''Read a SNP from an in memory row and returns chrom and document to index.'''
        chrom, start, end, rsid = row[0], int(row[1]), int(row[2]), row[3]
        if start == end:
            end = end + 1
        snp_doc = {
            'rsid': rsid,
            'chrom': chrom,
            'coordinates': {
                'gte': start,
                'lt': end
            },
        }
        info_tags = row[8].split(';')
        try:
            freq_tag = [
                tag for tag in info_tags if tag.startswith('FREQ=')
            ][0][5:]
        except IndexError:
            freq_tag = None
        if freq_tag:
            ref_allele_freq_map = {row[5]: {}}
            alt_alleles = row[6].split(',')
            alt_allele_freq_map = {}
            alt_allele_freqs = set()
            for population_freq in freq_tag.split('|'):
                population, freqs = population_freq.split(':')
                ref_freq, *alt_freqs = freqs.split(',')
                try:
                    ref_allele_freq_map[row[5]][population] = float(ref_freq)
                except ValueError:
                    pass
                for allele, freq_str in zip(alt_alleles, alt_freqs):
                    alt_allele_freq_map.setdefault(allele, {})
                    try:
                        freq = float(freq_str)
                    except (TypeError, ValueError):
                        continue
                    alt_allele_freqs.add(freq)
                    alt_allele_freq_map[allele][population] = freq
            snp_doc['ref_allele_freq'] = ref_allele_freq_map
            snp_doc['alt_allele_freq'] = alt_allele_freq_map
            if alt_allele_freqs:
                snp_doc['maf'] = max(alt_allele_freqs)
        return (chrom, snp_doc)

    # TODO: support bigBeds
    # def bb_region(self, row):
    #     '''Read a region from a bigBed file read with "pyBigWig" and returns document to index.'''
    #     start, end = int(row[0]), int(row[1])
    #     return {'start': start + 1, 'end': end}  # bed loc 'half-open', but we will close it

    # TODO: support bigBeds
    # def bb_snp(self, row):
    #     '''Read a SNP from a bigBed file read with "pyBigWig"  and returns document to index.'''
    #     start, end = int(row[0]), int(row[1])
    #     extras = row[3].split('\t')
    #     rsid = extras[0]
    #     num_score = int(extras[1])
    #     score = extras[2]
    #     start, end, rsid = row[0], int(row[0]), int(row[2]), row[3]
    #     return {'rsid': rsid, 'chrom': chrom, 'start': start + 1, 'end': end,
    #             'num_score': num_score, 'score': score}


class RegionIndexerState(IndexerState):
    # Accepts handoff of uuids from primary indexer. Keeps track of uuids and state by cycle.
    def __init__(self, es, key):
        super(RegionIndexerState, self).__init__(es, key, title='region')
        self.files_added_set = self.title + '_files_added'
        self.files_dropped_set = self.title + '_files_dropped'
        self.success_set = self.files_added_set
        # Clean these at beginning of next cycle:
        self.cleanup_last_cycle.extend([self.files_added_set, self.files_dropped_set])
        # DO NOT INHERIT! These keys are for passing on to other indexers
        self.followup_prep_list = None  # No followup to a following indexer
        self.staged_cycles_list = None  # Will take all of primary self.staged_for_regions_list

    def file_added(self, uuid):
        self.list_extend(self.files_added_set, [uuid])

    def file_dropped(self, uuid):
        self.list_extend(self.files_added_set, [uuid])

    @staticmethod
    def all_indexable_uuids_set(request):
        '''returns set of uuids. allowing intersections.'''
        return set(regulome_regionable_datasets(request))  # Uses elasticsearch query

    def all_indexable_uuids(self, request):
        '''returns list of uuids pertinant to this indexer.'''
        return list(self.all_indexable_uuids_set(request))

    def priority_cycle(self, request):
        '''Initial startup, reindex, or interupted prior cycle can all lead to a priority cycle.
           returns (priority_type, uuids).'''
        # Not yet started?
        initialized = self.get_obj("indexing")  # http://localhost:9200/snovault/meta/indexing
        self.is_reindexing = self._get_is_reindex()
        if not initialized:
            self.is_initial_indexing = True
            self.delete_objs([self.override])
            staged_count = self.get_count(self.staged_for_regions_list)
            if staged_count > 0:
                log.warn('Initial indexing handoff almost dropped %d staged uuids' % (staged_count))
            state = self.get()
            state['status'] = 'uninitialized'
            self.put(state)
            return ("uninitialized", [])
            # primary indexer will know what to do and region indexer should do nothing yet

        # Is a full indexing underway
        primary_state = self.get_obj("primary_indexer")
        if primary_state.get('cycle_count', 0) > SEARCH_MAX:
            return ("uninitialized", [])

        # Rare call for reindexing...
        reindex_uuids = self.reindex_requested(request)
        if reindex_uuids is not None and reindex_uuids != []:
            uuids_count = len(reindex_uuids)
            log.warn('%s reindex of %d uuids requested with force' % (self.state_id, uuids_count))
            return ("reindex", reindex_uuids)

        if self.get().get('status', '') == 'indexing':
            uuids = self.get_list(self.todo_set)
            log.info('%s restarting on %d datasets' % (self.state_id, len(uuids)))
            return ("restart", uuids)

        return ("normal", [])

    def get_one_cycle(self, request):
        '''Returns set of uuids to do this cycle and whether they should be forced.'''

        # never indexed, request for full reindex?
        (status, uuids) = self.priority_cycle(request)
        if status == 'uninitialized':
            return ([], False)            # Until primary_indexer has finished, do nothing!

        if len(uuids) > 0:
            if status == "reindex":
                return (uuids, True)
            if status == "restart":  # Restart is fine... just do the uuids over again
                return (uuids, False)
        assert(uuids == [])

        # Normal case, look for uuids staged by primary indexer
        staged_list = self.get_list(self.staged_for_regions_list)
        if not staged_list or staged_list == []:
            return ([], False)            # Nothing to do!
        self.delete_objs([self.staged_for_regions_list])  # TODO: tighten with locking semaphore

        # we don't need no stinking xmins... just take the whole set of uuids
        uuids = []
        for val in staged_list:
            if val.startswith("xmin:"):
                continue
            else:
                uuids.append(val)

        if len(uuids) > 500:  # some arbitrary cutoff.
            # There is an efficiency trade off examining many non-dataset uuids
            # # vs. the cost of eliminating those uuids from the list ahead of time.
            uuids = list(self.all_indexable_uuids_set(request).intersection(uuids))

        return (list(set(uuids)), False)  # Only unique uuids

    def finish_cycle(self, state, errors=None):
        '''Every indexing cycle must be properly closed.'''

        if errors:  # By handling here, we avoid overhead/concurrency issues of uuid-level accting
            self.add_errors(errors)

        # cycle-level accounting so todo => done => last in this function
        # self.rename_objs(self.todo_set, self.done_set)
        # done_count = self.get_count(self.todo_set)
        state.pop('cycle_count', None)
        self.rename_objs(self.todo_set, self.last_set)

        added = self.get_count(self.files_added_set)
        dropped = self.get_count(self.files_dropped_set)
        state['indexed'] = added + dropped

        # self.rename_objs(self.done_set, self.last_set)
        # cycle-level accounting so todo => done => last in this function
        self.delete_objs(self.cleanup_this_cycle)
        state['status'] = 'done'
        state['cycles'] = state.get('cycles', 0) + 1
        state['cycle_took'] = self.elapsed('cycle')

        self.put(state)
        self._del_is_reindex()
        return state

    @staticmethod
    def counts(region_es, assemblies=None):
        '''returns counts (region files, regulome files, snp files and all files)'''
        counts = {}
        try:
            counts['all_files'] = region_es.count(
                index=RESIDENT_REGIONSET_KEY,
            ).get('count', 0)
        except Exception:
            counts['all_files'] = 0

        if assemblies:
            counts['SNPs'] = {}
            for assembly in assemblies:
                try:
                    counts['SNPs'][assembly] = \
                        region_es.count(index=snp_index_key(assembly)).get('count', 0)
                except Exception:
                    counts['SNPs'][assembly] = 0

        return counts

    def display(self, uuids=None):
        display = super(RegionIndexerState, self).display(uuids=uuids)
        display['staged_to_process'] = self.get_count(self.staged_cycles_list)
        display['files_added'] = self.get_count(self.files_added_set)
        display['files_dropped'] = self.get_count(self.files_dropped_set)
        return display


@view_config(route_name='_regionindexer_state', request_method='GET', permission="index")
def regionindexer_state_show(request):
    encoded_es = request.registry[ELASTIC_SEARCH]
    encoded_INDEX = request.registry.settings['snovault.elasticsearch.index']
    regions_es = request.registry[SNP_SEARCH_ES]
    state = RegionIndexerState(encoded_es, encoded_INDEX)
    if not state.get():
        return "%s is not in service." % (state.state_id)
    # requesting reindex
    reindex = request.params.get("reindex")
    if reindex is not None:
        msg = state.request_reindex(reindex)
        if msg is not None:
            return msg

    # Requested notification
    who = request.params.get("notify")
    bot_token = request.params.get("bot_token")
    if who is not None or bot_token is not None:
        notices = state.set_notices(request.host_url, who, bot_token, request.params.get("which"))
        if notices is not None:
            return notices
    # Note: if reindex=all then maybe we should delete the entire region_index
    # On the otherhand, that should probably be left for extreme cases done by hand
    # curl -XDELETE http://localhost:9201/resident_datasets/
    # curl -XDELETE http://localhost:9201/chr*/

    display = state.display(uuids=request.params.get("uuids"))
    counts = state.counts(regions_es, REGULOME_SUPPORTED_ASSEMBLIES)
    display['files_in_index'] = counts.get('all_files', 0)
    display['snps_in_index'] = counts.get('SNPs', 0)

    if not request.registry.settings.get('testing', False):  # NOTE: _indexer not working on local
        try:
            r = requests.get(request.host_url + '/_regionindexer')
            display['listener'] = json.loads(r.text)
            display['status'] = display['listener']['status']
        except Exception:
            log.error('Error getting /_regionindexer', exc_info=True)

    # always return raw json
    if len(request.query_string) > 0:
        request.query_string = "&format=json"
    else:
        request.query_string = "format=json"
    return display


@view_config(route_name='index_region', request_method='POST', permission="index")
def index_regions(request):
    encoded_es = request.registry[ELASTIC_SEARCH]
    encoded_INDEX = request.registry.settings['snovault.elasticsearch.index']
    request.datastore = 'elasticsearch'  # Let's be explicit
    dry_run = request.json.get('dry_run', False)
    indexer = request.registry['region' + INDEXER]
    uuids = []

    # keeping track of state
    state = RegionIndexerState(encoded_es, encoded_INDEX)
    result = state.get_initial_state()

    (uuids, force) = state.get_one_cycle(request)
    state.log_reindex_init_state()
    # Note: if reindex=all_uuids then maybe we should delete the entire index
    # On the otherhand, that should probably be left for extreme cases done by hand
    # curl -XDELETE http://region-search-test-v5.instance.encodedcc.org:9200/resident_datasets/
    # if force == 'all':  # Unfortunately force is a simple boolean
    #    try:
    #        r = indexer.regions_es.indices.delete(index='chr*')  # Note region_es and encoded_es may be the same!
    #        r = indexer.regions_es.indices.delete(index=self.residents_index)
    #    except:
    #        pass

    uuid_count = len(uuids)
    if uuid_count > 0 and not dry_run:
        log.info("Region indexer started on %d uuid(s)" % uuid_count)

        result = state.start_cycle(uuids, result)
        errors = indexer.update_objects(request, uuids, force)
        result = state.finish_cycle(result, errors)
        if errors:
            result['errors'] = errors
        if result['indexed'] == 0:  # not unexpected, but worth logging otherwise silent cycle
            log.warn("Region indexer added %d file(s) from %d dataset uuids",
                     result['indexed'], uuid_count)
        else:
            regions_es = request.registry[SNP_SEARCH_ES]
            try:
                regions_es.indices.flush_synced(index='chr*')
                regions_es.indices.flush_synced(index=SNP_INDEX_PREFIX + '*')
                regions_es.indices.flush_synced(index=RESIDENT_REGIONSET_KEY)
            except Exception:
                pass

    state.send_notices()
    return result


class RegionIndexer(Indexer):
    def __init__(self, registry):
        super(RegionIndexer, self).__init__(registry)
        self.encoded_es = registry[ELASTIC_SEARCH]    # yes this is self.es but we want clarity
        self.encoded_INDEX = registry.settings['snovault.elasticsearch.index']
        self.regions_es = registry[SNP_SEARCH_ES]
        self.residents_index = RESIDENT_REGIONSET_KEY
        # WARNING: updating 'state' could lead to race conditions if more than 1 worker
        self.state = RegionIndexerState(self.encoded_es, self.encoded_INDEX)
        self.reader = RemoteReader()

    def update_objects(self, request, uuids, force):
        # pylint: disable=too-many-arguments, unused-argument
        '''Run indexing process on uuids'''
        errors = []
        for i, uuid in enumerate(uuids):
            error = self.update_object(request, uuid, force)
            if error is not None:
                errors.append(error)
            if (i + 1) % 1000 == 0:
                log.info('Indexing %d', i + 1)
        return errors

    def update_object(self, request, dataset_uuid, force):
        request.datastore = 'elasticsearch'  # Let's be explicit

        last_exc = None
        try:
            # less efficient than going to es directly but keeps methods in one place
            dataset = request.embed(str(dataset_uuid), as_user=True)
        except StatementError:
            # Can't reconnect until invalid transaction is rolled back
            raise
        except Exception as e:
            log.warn("dataset is not found for uuid: %s", dataset_uuid)
            last_exc = repr(e)

        if last_exc is None and not self.is_candidate_dataset(dataset):
            return  # Note if dataset is NO LONGER a candidate its files won't get removed.

        if last_exc is None:
            files = dataset.get('files', [])
            candidate_files = []
            released_only = False
            for afile in files:
                # files may not be embedded
                if isinstance(afile, str):
                    file_id = afile
                    try:
                        afile = request.embed(file_id, as_user=True)
                    except StatementError:
                        # Can't reconnect until invalid transaction is rolled back
                        raise
                    except Exception as e:
                        log.warn("file %s of dataset %s is not found; "
                                 "skip the rest of files in this dataset.",
                                 file_id, dataset_uuid)
                        last_exc = repr(e)
                        break

                if afile.get('file_format') not in ALLOWED_FILE_FORMATS:
                    continue  # Note: if file_format changed, it doesn't get removed from region index.

                if self.is_candidate_file(request, afile, dataset):
                    candidate_files.append(afile)
                    if afile.get('status', 'unknown') == 'released':
                        released_only = True
                else:
                    if self.remove_from_regions_es(afile['uuid']):
                        log.warn("dropped file: %s %s", dataset['accession'], afile['@id'])
                        self.state.file_dropped(afile['uuid'])

        if last_exc is None:
            for afile in candidate_files:
                if released_only and afile.get('status', 'unknown') != 'released':
                    continue
                file_uuid = afile['uuid']
                file_doc = self.metadata_doc(afile, dataset)
                using = ""
                if force:
                    using = "with FORCE"
                    self.remove_from_regions_es(file_uuid)  # remove all regions first
                else:
                    if self.in_regions_es(file_uuid):
                        # TODO: update residence doc but not file!
                        continue

                try:
                    self.add_file_to_regions_es(request, afile, file_doc)
                except Exception as e:
                    log.warn("Fail to index file %s of dataset %s; "
                             "skip the rest of files in this dataset.",
                             file_uuid, dataset_uuid)
                    last_exc = repr(e)
                    break
                else:
                    log.info("added file: %s %s %s", dataset['accession'], afile['href'], using)
                    self.state.file_added(file_uuid)

        if last_exc is not None:
            timestamp = datetime.datetime.now().isoformat()
            return {'error_message': last_exc, 'timestamp': timestamp, 'uuid': str(dataset_uuid)}

    @staticmethod
    def check_embedded_targets(request, dataset):
        '''Make sure taget or targets is embedded.'''
        # Not all datasets will have a target but if they do it must be embeeded
        target = dataset.get('target')
        if target is not None:
            if not isinstance(target, str):
                return target
            else:
                try:
                    return request.embed(target, as_user=True)
                except Exception:
                    log.warn("Target is not found for: %s", dataset['@id'])
                    return None
        else:
            targets = dataset.get('targets', [])
            if len(targets) > 0:
                if isinstance(targets[0], dict):
                    return targets
                target_objects = []
                for targ in targets:
                    if isinstance(targets[0], str):
                        try:
                            target_objects.append(request.embed(targ, as_user=True))
                        except Exception:
                            log.warn("Target %s is not found for: %s" % (targ, dataset['@id']))
                return target_objects

        return None

    @staticmethod
    def is_candidate_dataset(dataset):
        '''returns None, or a list of uses which may include region search 
        and/or regulome.
        '''

        if not (set(REGULOME_DATASET_TYPES) & set(dataset['@type'])):
            return False
        if len(dataset.get('files', [])) == 0:
            return False
        collection_type = regulome_collection_type(dataset)
        if collection_type not in REGULOME_REGION_REQUIREMENTS:
            return False
        # REG-14 special case for indexing dbSNP v153 only
        if collection_type == 'index' and (
            'RegulomeDB' not in dataset.get('internal_tags', [])
            or dataset['status'] != 'released'
        ):
            return False
        # REG-186 special case for chromatin state data since new data is not
        # compatible with current regulome model.
        if (
            collection_type == 'chromatin state'
            and 'RegulomeDB' not in dataset.get('internal_tags', [])
        ):
            return False
        return True

    @staticmethod
    def metadata_doc(afile, dataset):
        '''returns file and dataset metadata document'''
        meta_doc = {
            'uuid': str(afile['uuid']),
            'uses': FOR_REGULOME_DB,
            'file': {
                'uuid': str(afile['uuid']),
                '@id': afile['@id'],
                'assembly': afile.get('assembly', 'unknown')
            },
            'dataset': {
                'uuid': str(dataset['uuid']),
                '@id': dataset['@id']
            }
        }

        # collection_type may be the first of these that are actually found
        for prop in REGULOME_COLLECTION_TYPES:
            prop_value = dataset.get(prop)
            if prop_value:
                meta_doc['dataset'][prop] = prop_value
                if 'collection_type' not in meta_doc['dataset']:
                    meta_doc['dataset']['collection_type'] = prop_value
        target = dataset.get('target', {})
        if target:  # overloaded target with potential list of target objects
            if isinstance(target, dict):
                target = [target]
            if isinstance(target, list):
                target_labels = []
                for targ in target:
                    genes = targ.get('genes')
                    if genes:
                        target_labels.extend([gene['symbol'].upper()
                                              for gene in genes])
                if len(target_labels) > 0:
                    meta_doc['dataset']['target'] = target_labels
        meta_doc['dataset']['biosample_ontology'] = dataset.get(
            'biosample_ontology', {}
        )
        meta_doc['dataset']['documents'] = []
        # Only save documents for datasets having motif info
        if meta_doc['dataset']['collection_type'] in ['Footprints', 'PWMs']:
            meta_doc['dataset']['documents'] = dataset.get('documents', [])
        biosample = dataset.get('biosample_ontology', {}).get('term_name', "None")
        if biosample:
            meta_doc['dataset']['biosample_term_name'] = biosample

        for dataset_type in REGULOME_DATASET_TYPES:  # prioritized
            if dataset_type in dataset['@type']:
                meta_doc['dataset_type'] = dataset_type
                break
        if dataset_type == 'Reference':
            meta_doc['snps'] = True
        return meta_doc

    def is_candidate_file(self, request, afile, dataset):
        '''returns None or a document with file details to save in the residence index'''
        if afile.get('href') is None:
            return False
        if afile['file_format'] not in ALLOWED_FILE_FORMATS:
            return False

        file_status = afile.get('status', 'imagined')
        assembly = afile.get('assembly', 'unknown')

        # dataset passed in can be file's dataset OR file_set, with each file pointing elsewhere
        if isinstance(afile['dataset'], dict) and afile['dataset']['@id'] != dataset['@id']:
            dataset = afile['dataset']
        elif isinstance(afile['dataset'], str) and afile['dataset'] != dataset['@id']:
            try:
                dataset = request.embed(afile['dataset'], as_user=True)
            except Exception:
                log.warn("dataset is not found: %s", afile['dataset'])
                return False
        target = self.check_embedded_targets(request, dataset)
        if target is not None:
            dataset['target'] = target

        if file_status in REGULOME_ALLOWED_STATUSES \
           and assembly in REGULOME_SUPPORTED_ASSEMBLIES:
            required_properties = REGULOME_REGION_REQUIREMENTS.get(
                regulome_collection_type(dataset)
            )
            if required_properties:
                return all(
                    afile.get(prop) in vals
                    for prop, vals in required_properties.items()
                )

        return False

    def in_regions_es(self, uuid, use_type=None):
        '''returns True if a uuid is in regions es'''
        try:
            if use_type is not None:
                doc = self.regions_es.get(index=self.residents_index, doc_type=use_type,
                                          id=str(uuid)).get('_source', {})
            else:
                doc = self.regions_es.get(index=self.residents_index, id=str(uuid)).get('_source', {})
            if doc:
                return True
        except NotFoundError:
            return False
        except Exception:
            pass

        return False

    def remove_from_regions_es(self, uuid):
        '''Removes all traces of a uuid (from file) from region search elasticsearch index.'''
        try:
            result = self.regions_es.get(index=self.residents_index, id=str(uuid))
            doc = result.get('_source', {})
            use_type = result.get('_type', FOR_REGULOME_DB)
            if not doc:
                log.warn("Trying to drop file: %s  NOT FOUND", uuid)
                return False
        except Exception:
            return False  # Not an error: remove may be called without looking first

        if 'index' in doc:
            try:
                self.regions_es.delete(index=doc['index'])
            except Exception:
                log.error("Region indexer failed to delete %s index" % (doc['index']))
                return False   # Will try next full cycle
        else:
            for chrom in doc['chroms']:  # Could just try index='chr*'
                try:
                    self.regions_es.delete(index=chrom.lower(), doc_type=doc['assembly'],
                                           id=str(uuid))
                except Exception:
                    # log.error("Region indexer failed to remove %s regions of %s" % (chrom, uuid))
                    # return False # Will try next full cycle
                    pass

        try:
            self.regions_es.delete(index=self.residents_index, doc_type=use_type, id=str(uuid))
        except Exception:
            log.error("Region indexer failed to remove %s from %s" % (uuid, self.residents_index))
            return False  # Will try next full cycle

        return True

    def add_to_residence(self, file_doc):
        '''Adds a file into residence index.'''
        uuid = file_doc['uuid']

        # Only splitting on doc_type=use in order to easily count them
        use_type = FOR_REGULOME_DB

        # Make sure there is an index set up to handle whether uuids are resident
        if not self.regions_es.indices.exists(self.residents_index):
            self.regions_es.indices.create(index=self.residents_index, body=index_settings())

        if not self.regions_es.indices.exists_type(index=self.residents_index, doc_type=use_type):
            mapping = get_resident_mapping(use_type)
            self.regions_es.indices.put_mapping(index=self.residents_index, doc_type=use_type,
                                                body=mapping)

        self.regions_es.index(index=self.residents_index, doc_type=use_type, body=file_doc,
                              id=str(uuid))
        return True

    @staticmethod
    def region_bulk_iterator(chrom, assembly, uuid, docs_for_chrom):
        '''Given yields peaks packaged for bulk indexing'''
        for idx, doc in enumerate(docs_for_chrom):
            doc['uuid'] = uuid
            yield {'_index': chrom, '_type': assembly, '_id': uuid+'-'+str(idx), '_source': doc}

    def index_regions(self, assembly, regions, file_doc, chroms):
        '''Given regions from some source (most likely encoded file)
           loads the data into region search es'''
        uuid = file_doc['uuid']

        if chroms is None:
            chroms = list(regions.keys())

        for chrom in list(regions.keys()):
            chrom_lc = chrom.lower()
            # Could be a chrom never seen before!
            if not self.regions_es.indices.exists(chrom_lc):
                self.regions_es.indices.create(index=chrom_lc, body=index_settings())

            if not self.regions_es.indices.exists_type(index=chrom_lc, doc_type=assembly):
                mapping = get_chrom_index_mapping(assembly)
                self.regions_es.indices.put_mapping(index=chrom_lc, doc_type=assembly, body=mapping)

            if len(regions[chrom]) == 0:
                continue
            bulk(self.regions_es,
                 self.region_bulk_iterator(chrom_lc, assembly, uuid, regions[chrom]), chunk_size=500000)

            file_doc['chroms'].append(chrom)

            try:  # likely millions per chrom, so
                self.regions_es.indices.flush_synced(index=chrom)
            except Exception:
                pass

        return True

    @staticmethod
    def snps_bulk_iterator(snp_index, chrom, snps_for_chrom):
        '''Given SNPs yields snps packaged for bulk indexing'''
        for snp in snps_for_chrom:
            yield {'_index': snp_index, '_type': chrom, '_id': snp['rsid'], '_source': snp}

    def index_snps(self, assembly, snps, file_doc, chroms=None):
        '''Given SNPs from file loads the data into region search es'''
        snp_index = snp_index_key(assembly)
        file_doc['index'] = snp_index

        if not self.regions_es.indices.exists(snp_index):
            self.regions_es.indices.create(index=snp_index, body=index_settings())

        if chroms is None:
            chroms = list(snps.keys())
        for chrom in chroms:
            if len(snps[chrom]) == 0:
                continue
            if not self.regions_es.indices.exists_type(index=snp_index, doc_type=chrom):
                mapping = get_snp_index_mapping(chrom)
                self.regions_es.indices.put_mapping(index=snp_index, doc_type=chrom, body=mapping)
            # indexing in bulk 500K snps at a time...
            bulk(self.regions_es,
                 self.snps_bulk_iterator(snp_index, chrom, snps[chrom]), chunk_size=500000)
            file_doc['chroms'].append(chrom)

            try:  # likely millions per chrom, so
                self.regions_es.indices.flush_synced(index=snp_index)
            except Exception:
                pass
            log.warn('Added %s/%s %d docs', snp_index, chrom, len(snps[chrom]))

        return True

    def add_file_to_regions_es(self, request, afile, file_doc, snp=False):
        '''Given an encoded file object, reads the file to create regions data
           then loads that into region search es.'''

        assembly = file_doc['file']['assembly']
        snp_set = file_doc.get('snps', False)
        # ############### TEMPORARY  because snps take so long!
        # if snp_set:
        #     file_doc['chroms'] = SUPPORTED_CHROMOSOMES
        #     file_doc['index'] = snp_index_key(assembly)
        #     return self.add_to_residence(file_doc)
        # ############### TEMPORARY
        big_file = (afile.get('file_size', 0) > MAX_IN_MEMORY_FILE_SIZE)
        file_doc['chroms'] = []

        readable_file = self.reader.readable_file(request, afile)

        file_data = {}
        chroms = []
        if afile['file_format'] == 'bed':
            # NOTE: requests doesn't require gzip but http.request does.
            with gzip.open(readable_file, mode='rt') as file_handle:
                for row in self.reader.tsv(file_handle):
                    if row[0].startswith('#'):
                        continue
                    try:
                        if snp_set:
                            (chrom, doc) = self.reader.snp(row)
                        else:
                            (chrom, doc) = self.reader.region(
                                row,
                                value_col=REGULOME_VALUE_STRAND_COL.get(
                                    file_doc['dataset']['collection_type'], {}
                                ).get('value_col'),
                                strand_col=REGULOME_VALUE_STRAND_COL.get(
                                    file_doc['dataset']['collection_type'], {}
                                ).get('strand_col')
                            )
                    except Exception:
                        log.error('%s - failure to parse row %s:%s:%s, skipping row',
                                  afile['href'], row[0], row[1], row[2])
                        continue
                    if doc['coordinates']['gte'] == doc['coordinates']['lt']:
                        log.error(
                            '%s - on chromosome %s, a start coordinate %s is '
                            'larger than or equal to the end coordinate %s, '
                            'skipping row',
                            afile['href'],
                            row[0],
                            row[1],
                            row[2]
                        )
                        continue  # Skip for 63 invalid peak in a non-ENCODE ChIP-seq result, exo_HelaS3.CTCF.bed.gz
                    if chrom not in SUPPORTED_CHROMOSOMES:
                        continue   # TEMPORARY: limit both SNPs and regions to major chroms
                    if (chrom not in file_data) or (len(file_data[chrom]) > MAX_SNP_BULK):
                        # we are done with current chromosome and move on
                        # 1 chrom at a time saves memory (but assumes the files are in chrom order!)
                        if big_file and file_data and len(chroms) > 0:
                            if snp_set:
                                self.index_snps(assembly, file_data, file_doc,
                                                list(file_data.keys()))
                            else:
                                self.index_regions(assembly, file_data, file_doc,
                                                   list(file_data.keys()))
                            file_data = {}  # Don't hold onto data already indexed
                        file_data[chrom] = []
                        if len(chroms) == 0 or chroms[-1] != chrom:
                            chroms.append(chrom)
                    file_data[chrom].append(doc)
        # TODO: Handle bigBeds...
        # elif afile['file_format'] == 'bedBed':  # Use pyBigWig?
        #    import pyBigWig  # https://github.com/deeptools/pyBigWig
        #    with pyBigWig.open(readable_file) as bb:
        #              # reader.readable_file must return remote url for bb files
        #        chroms = bb.chroms()
        #        for chrom in chroms.keys():  # should sort
        #            for row in bb.entries(chrom, 0, chroms[chrom], withString=snp_set):
        #                try:
        #                    if snp_set:
        #                        doc = self.reader.bb_snp(row)
        #                    else:
        #                        doc = self.reader.bb_region(row)
        #                except Exception:
        #                    log.error('%s - failure to parse row %s:%s:%s, skipping row', \
        #                                                    afile['href'], chrom, row[0], row[1])
        # Could redesign with reader class, so this function is entirely ignorant of bed v. bigBed
        # However, probably not worth as much as just abstracting the file_data building/indexing

        if len(chroms) == 0 or not file_data:
            raise IOError('Error parsing file %s' % afile['href'])

        # Note if indexing by chrom (snp_set or big_file) then file_data will only have one chrom
        if snp_set:
            self.index_snps(assembly, file_data, file_doc, list(file_data.keys()))
        else:
            self.index_regions(assembly, file_data, file_doc, list(file_data.keys()))

        if big_file and file_doc['chroms'] != chroms:
            log.error('%s chromosomes %s indexed out of order!', file_doc['file']['@id'],
                      ('SNPs' if snp_set else 'regions'))
        return self.add_to_residence(file_doc)
