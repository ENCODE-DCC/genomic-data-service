import time
import requests
import pprint

n = 1
test_snp_dict = {
    "rs4385801": ("chr10", 127511789, 127511790),
    "rs2067749": ("chr9", 33130639, 33130640),
    "rs11826681": ("chr11", 30344882, 30344883),
    "rs675713": ("chr9", 136574592, 136574593),
    "rs4284503": ("chr13", 111124254, 111124255),
    "rs2647046": ("chr6", 32668335, 32668336),
    "rs60093835": ("chr22", 39493355, 39493356),
    "rs4142893": ("chr9", 126980356, 126980357),
    "rs10937924": ("chr4", 3374897, 3374898),
    "rs1487433": ("chr18", 21591999, 21592000),
    "rs1129593": ("chr12", 105380151, 105380152),
    "rs1860870": ("chr7", 150430710, 150430711),
    "rs10829219": ("chr10", 27560119, 27560120),
    "rs34161004": ("chr15", 93239387, 93239388),
    "rs386542921": ("chr19", 58685050, 58685051),
    "rs1134924": ("chr5", 179126089, 179126090),
    "rs7170947": ("chr15", 50399671, 50399672),
    "rs11121317": ("chr1", 9138466, 9138467),
    "rs61743574": ("chr7", 114562422, 114562423),
    "rs2272744": ("chr4", 4250132, 4250133),
    "rs7563337": ("chr2", 75658963, 75658964),
    "rs7177778": ("chr15", 81626399, 81626400),
    "rs17635335": ("chr10", 126417180, 126417181),
    "rs72891915": ("chr6", 33476199, 33476200),
    "rs8092180": ("chr18", 34586879, 34586880),
    "rs72845039": ("chr6", 27560874, 27560875),
    "rs1260460": ("chr9", 6631098, 6631099),
    "rs16901784": ("chr6", 26555432, 26555433),
    "rs4481616": ("chr8", 126311068, 126311069),
    "rs55757812": ("chr2", 56336112, 56336113),
    "rs6533945": ("chr4", 116860122, 116860123),
    "rs34075941": ("chr1", 175243580, 175243581),
    "rs35350109": ("chr5", 116583758, 116583759),
    "rs1075621": ("chr9", 140779260, 140779261),
    "rs1976938": ("chr12", 53661924, 53661925),
    "rs4750690": ("chr10", 130010322, 130010323),
    "rs73057551": ("chr3", 28078189, 28078190),
    "rs4490404": ("chr3", 46101370, 46101371),
    "rs4945684": ("chr6", 121717494, 121717495),
    "rs56027645": ("chr19", 54998092, 54998093),
    "rs7168659": ("chr15", 52016498, 52016499),
    "rs3912121": ("chr3", 137051115, 137051116),
    "rs1571702": ("chr21", 38337195, 38337196),
    "rs2300905": ("chr6", 88204830, 88204831),
    "rs1883839": ("chr20", 39342791, 39342792),
    "rs634512": ("chr12", 69754011, 69754012),
    "rs4970774": ("chr1", 110268827, 110268828),
    "rs1854962": ("chr1", 110269285, 110269286),
    "rs634514": ("chr12", 69754016, 69754017),
    "rs4496503": ("chr3", 128210062, 128210063),
    "rs16978757": ("chr19", 12995421, 12995422),
    "rs2072597": ("chr19", 12996739, 12996740),
    "rs79334031": ("chr19", 12998101, 12998102),
    "rs9825813": ("chr3", 128211243, 128211244),
    "rs117351327": ("chr19", 12996718, 12996719),
    "rs3922557": ("chr3", 128210025, 128210026),
    "rs1986452": ("chr3", 128210341, 128210342),
    "rs11712335": ("chr3", 128210549, 128210550),
    "rs116136295": ("chr3", 128211665, 128211666),
    "rs16978754": ("chr19", 12995402, 12995403),
    "rs2072596": ("chr19", 12996499, 12996500),
    "rs112631212": ("chr19", 12996928, 12996929),
    "rs10407416": ("chr19", 12997732, 12997733),
    "rs3817621": ("chr19", 12998204, 12998205),
    "rs11101993": ("chr1", 110269187, 110269188),
    "test1": ("chr10", 11741181, 11741181),
    "test2": ("chr10", 64353900, 64353900),
    "test3": ("chr1", 39492462, 39492462),
}

test_url = "http://localhost:9201/{}/_search"
clear_cache_url = "http://localhost:9201/_cache/clear"
start = 0
end = 0
start_cond = {"lt": end}
end_cond = {"gte": start}
SEARCH_MAX = 99999

query_tim = {
    "query": {
        "bool": {
            "filter": {
                "nested": {
                    "inner_hits": {"size": SEARCH_MAX},
                    "path": "positions",
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "must": [
                                            {"range": {"positions.start": start_cond}},
                                            {"range": {"positions.end": end_cond}},
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                }
            }
        }
    },
    "size": SEARCH_MAX,
    "_source": False,  # True is snps, False if regions
}

query_filter = {
    "query": {"term": {"coordinates": {}}},
    "size": SEARCH_MAX,
}

query_no_filter = {
    "query": {
        "nested": {
            "inner_hits": {"size": SEARCH_MAX},
            "path": "positions",
            "query": {
                "bool": {
                    "must": [
                        {"range": {"positions.start": start_cond}},
                        {"range": {"positions.end": end_cond}},
                    ]
                }
            },
        }
    },
    "size": SEARCH_MAX,
    "_source": False,
}

query_no_filter_with_uuid = {
    "query": {
        "nested": {
            "inner_hits": {"size": SEARCH_MAX},
            "path": "positions",
            "query": {
                "bool": {
                    "must": [
                        {"range": {"positions.start": start_cond}},
                        {"range": {"positions.end": end_cond}},
                    ]
                }
            },
        }
    },
    "size": SEARCH_MAX,
    "_source": "uuid",
}

query_dict = {
    "Tim": query_tim,
    "Filter": query_filter,
    "No Filter": query_no_filter,
    "No Filter Get UUID": query_no_filter_with_uuid,
}


def main():
    for label, query in {"Filter": query_filter}.items():
        python_time = 0
        es_time = 0
        tot_time = 0
        print("Clear all caches:", requests.post(clear_cache_url))
        print("Rsid\tChr\tes_time\tnHits")
        for rsid, (chrom, start, end) in test_snp_dict.items():
            for i in range(n):
                es_time = 0
                query["query"]["term"]["coordinates"]["value"] = start
                begin = time.time()
                res = requests.get(test_url.format(chrom), json=query).json()
                python_time += time.time() - begin
                try:
                    es_time = res["took"]
                    tot_time += es_time
                    nhits = len(res["hits"]["hits"])
                    if nhits > 0:
                        print(
                            "{rs}\t{ch}\t{time:4.2f}\t{nhit:5d}".format(
                                rs=rsid, ch=chrom, time=es_time, nhit=nhits
                            )
                        )
                        # pprint.pprint(res.get('hits', ""), indent=4)
                except KeyError:
                    print("query failed: {}".format(res["error"]["reason"]))
        print(
            "### Average python time {} (ms): {}".format(
                label, 1000 * python_time / (n * len(test_snp_dict))
            )
        )
        print(
            "### Average elasticsearch time {} (ms): {}".format(
                label, tot_time / (n * len(test_snp_dict))
            )
        )
        pprint.pprint(query, indent=4)


if __name__ == "__main__":
    main()
