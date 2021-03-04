import os
import json
import subprocess

from pyserini.util import get_cache_home
from pyserini.util import download_evaluation_script


def _topic_process__ntcir12_math_browsing(line):
    fields = line.split()
    query = [{'type': 'tex', 'keyword': ' '.join(fields[1:])}]
    qid = fields[0]
    return qid, query


def _topic_process__ntcir12_math_browsing_concrete(line):
    fields = line.split()
    query = [{'type': 'tex', 'keyword': ' '.join(fields[1:])}]
    qid = fields[0]
    return qid, query


def _topic_process__ntcir12_math_browsing_wildcards(line):
    fields = line.split()
    query = [{'type': 'tex', 'keyword': ' '.join(fields[1:])}]
    qid = fields[0]
    return qid, query


def _topic_process__arqmath_2020_task1(json_item):
    query = [{'type': kw['type'], 'keyword': kw['str']} for kw in json_item['kw']]
    qid = 'A.' + str(json_item['qid'])
    return qid, query


def gen_topics_queries(collection: str):
    func_name = '_topic_process__' + collection.replace('-', '_')
    handler = globals()[func_name] if func_name in globals() else None
    cache = get_cache_home()
    prefix = f'./tools/topics-and-qrels/topics.{collection}'
    found = False
    for src in [f'{prefix}.{ent}' for ent in ['txt', 'json']]:
        if not os.path.exists(src):
            continue
        else:
            found = True
        ext = src.split('.')[-1]
        if ext == 'txt':
            with open(src, 'r') as fh:
                for line in fh:
                    line = line.rstrip()
                    yield handler(line)
        elif ext == 'json':
            with open(src, 'r') as fh:
                qlist = json.load(fh)
                for json_item in qlist:
                    yield handler(json_item)
    if not found:
        raise ValueError(f'Unrecognized index name {collection}')


def get_qrels_filepath(collection: str):
    path = f'./tools/topics-and-qrels/qrels.{collection}.txt'
    if os.path.exists(path):
        return path
    else:
        return None


def trec_eval(qrels: str, run: str, eval_args: str):
    extra_args = eval_args.split() if eval_args else []
    cmd = ['./tools/eval/trec_eval.9.0.4/trec_eval', qrels, run, *extra_args]
    print(f'Invoking trec_eval: {cmd}', end='')
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stderr.decode("utf-8"), end='')
    return stdout.decode("utf-8")
