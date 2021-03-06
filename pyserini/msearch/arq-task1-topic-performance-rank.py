import json

if False:
    input_file = "./a0-ndcg.txt"
else:
    input_file = './mdowsers-ndcg.txt'

topics_file = './tools/topics-and-qrels/topics.arqmath-2020-task1.json'

with open(topics_file, 'r') as fh:
    topics = json.load(fh)
    inv_topics = {'A.' + str(topic['qid']): topic['kw'] for topic in topics}
    #print(inv_topics)

with open(input_file, 'r') as fh:
    for line in fh:
        line = line.rstrip()
        fields = line.split()
        qryID = fields[1]
        ndcg = fields[2]
        kw = inv_topics[qryID]
        print(qryID, ndcg, [k['str'] for k in kw if k['type'] == 'tex'])
