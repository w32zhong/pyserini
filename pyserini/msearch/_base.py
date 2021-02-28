import os
import subprocess

from pyserini.util import get_cache_home
from pyserini.util import download_evaluation_script

def _line_process__ntcir12_math_browsing(line):
    fields = line.split()
    query = [{'type': 'tex', 'keyword': fields[1]}]
    qid = fields[0]
    return qid, query


def gen_topics_queries(collection: str):
    cache = get_cache_home()
    src = f'./tools/topics-and-qrels/topics.{collection}.txt'
    with open(src, 'r') as fh:
        for line in fh:
            line = line.rstrip()
            func_name = '_line_process__' + collection.replace('-', '_')
            handler = globals()[func_name]
            yield handler(line)


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
