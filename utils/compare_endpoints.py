import requests
import logging
import sys
from deepdiff import DeepDiff
from pprint import pprint

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

SOURCE = 'https://www.regulomedb.org/regulome-'
TARGET = 'http://localhost:5000/'


def compare(path):
    target = requests.get(TARGET + path).json()
    source = requests.get(SOURCE + path).json()

    ignore_fields = ['@id', '@type', 'context', 'title', 'timing']

    pprint(DeepDiff(source, target, exclude_paths=[
           "root['" + f + "']" for f in ignore_fields]), indent=2)

    import pdb
    pdb.set_trace()


if __name__ == '__main__':
    compare('summary/?regions=rs3768324%0D%0Ars75982468%0D%0Ars10905307%0D%0Ars10823321%0D%0Ars7745856&genome=GRCh37&maf=0.01&format=json')
