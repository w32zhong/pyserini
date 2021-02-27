from pyserini.search import SimpleSearcher
from pyserini.index import IndexReader

#SimpleSearcher.list_prebuilt_indexes()

#searcher = SimpleSearcher.from_prebuilt_index('trec-covid-r1-abstract')
searcher = SimpleSearcher('./indexes/tiny.lucene')
index_reader = IndexReader('./indexes/tiny.lucene')

stats = index_reader.stats()

#for i in range(stats['documents']):
#    doc = searcher.doc(i)
#    print(f'--- doc#{i} ---')
#    print(doc.contents())
#    #print(doc.raw())

print('=== searching... ===')
hits = searcher.search('coast')
for i, hit in enumerate(hits):
    print(f'{i+1:2} doc#{hit.docid:7} {hit.score:.5f}')
    doc = searcher.doc(hit.docid)
    print(doc.contents())
