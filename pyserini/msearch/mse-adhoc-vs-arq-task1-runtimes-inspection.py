import json

do_json = True

if do_json:
    topics_file = 'tools/topics-and-qrels/topics.arqmath-2020-task1.json'
    runtimes_file = 'runs/arqmath-2020-task1-K1000.2.runtimes'
else:
    topics_file = 'tools/topics-and-qrels/topics.ntcir12-math-browsing-concrete.txt'
    runtimes_file = 'runs/mse-ecir2020-K1000.overall.runtimes'

with open(topics_file, 'r') as fh:
    if do_json:
        topics = json.load(fh)
    else:
        topics = []
        for line in fh:
            line = line.rstrip()
            fields = line.split('\t')
            tex = fields[1]
            topics.append({
                'kw': [{
                    'type': 'tex',
                    'str': tex
                }]
            })

with open(runtimes_file, 'r') as fh:
    j = json.load(fh)
    runtimes = j['runtimes']

qr_pairs = [(i, topics[i]['kw'], runtime) for i, runtime in enumerate(runtimes)]

texlen = 0
for j, (_, topic, runtime) in enumerate(sorted(qr_pairs, key=lambda x: x[2])):
    #print(runtime, [kw['type'] + f'-{len(kw["str"])}' for kw in topic])
    texlen += sum([len(kw['str']) for kw in topic if kw['type'] == 'tex'])
    #print(runtime, topic[0]["str"])
    print(runtime, [kw['str'] for kw in topic if kw['type'] == 'tex'])
    #if j != -1 and j != 19:
    #    print(str(runtime)+',',end='')

print(texlen / len(qr_pairs))
