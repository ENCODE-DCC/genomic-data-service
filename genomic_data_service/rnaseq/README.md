## Index RNA expression data
Run in screen session. Specify the Elasticsearch location using `--host` option (e.g. `localhost:9202` or `vpc-rna-expression.es.amazonaws.com:9200`).
```bash
$ source genomic-venv/bin/activate
$ python3 genomic_data_service/rnaseq/commands/index_rna_seq_data.py --host [HOST]
...
indexing /files/ENCFF702ALH/
getting items
got items 59526
bulk loading
done bulk loading 9.511317491531372
...
```

## Optimize index
Index refresh is turned off to maximize life of aggregation cache. After fully indexing force merge segments
and refresh once. Force merge is expensive operation that requires disk space.
```bash
$ curl -X POST "[HOST]/rna-expression/_forcemerge?max_num_segments=1&pretty"
$ curl -X POST "[HOST]/rna-expression/_refresh?pretty"
```

## Notes
- Warm up cache by clicking on different facet combinations.
- Check `request_cache` stats for memory usage and cache evictions:
```bash
$ curl -X GET "[HOST]/_stats/request_cache?pretty&human"
```

## Tests
Run tests for indexing code.
```bash
$ pytest -s -k 'test_rnaseq_'
```
