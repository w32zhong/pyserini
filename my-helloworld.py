from pyserini.search import SimpleSearcher

SimpleSearcher.list_prebuilt_indexes()

searcher = SimpleSearcher.from_prebuilt_index('trec-covid-r1-abstract')
hits = searcher.search('covid')
for i in range(0, 10):
    print(f'{i+1:2} {hits[i].docid:7} {hits[i].score:.5f}')
