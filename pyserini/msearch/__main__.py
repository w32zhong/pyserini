#
# Pyserini: Python interface to the Anserini IR toolkit built on Lucene
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import os
import sys
import tempfile

from pyserini.msearch import MathSearcher
from pyserini.msearch import gen_topics_queries, get_qrels_filepath, trec_eval


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Conduct math-aware search using Approach0 search engine')

    parser.add_argument('--query', type=str, required=False, nargs='+',
        help="Mixed type of keywords, math keywords are written in TeX and wrapped up in dollars")
    parser.add_argument('--docid', type=int, required=False,
        help="Lookup a raw document from index")
    parser.add_argument('--index', type=str, required=False,
        help="Open index at specified path or from a prebuilt index")
    parser.add_argument('--topk', type=int, required=False,
        help="Keep at most top-K hits in results")
    parser.add_argument('--trec-output', type=str, required=False,
        help="Output TREC-format results")
    parser.add_argument('--verbose', required=False, action='store_true',
        help="Verbose output (showing query structures and merge times)")
    parser.add_argument('--list-prebuilt-indexes', required=False,
        action='store_true', help="List available prebuilt math indexes and abort")
    parser.add_argument('--eval-math-collection', type=str, required=False,
        help="Evaluate TREC output using specified math collection qrels/topics")
    parser.add_argument('--eval-args', type=str, required=False,
        help="Passing extra command line arguments to trec_eval. E.g., '-q -m map -m P.30'")

    args = parser.parse_args()
    #print(args)

    if (args.list_prebuilt_indexes):
        MathSearcher.list_prebuilt_indexes()
        exit(0)

    # create searcher from specified index path
    if not os.path.exists(args.index):
        searcher = MathSearcher.from_prebuilt_index(args.index)
        if searcher is None: # if index name is not registered
            exit(1)
    else:
        searcher = MathSearcher(args.index)

    # overwrite default arguments for running searcher
    verbose = args.verbose if args.verbose else False
    topk = args.topk if args.topk else 20
    trec_output_specified = True if args.trec_output else False
    trec_output = args.trec_output if args.trec_output else '/dev/null'

    if args.query:
        # parser query by different types
        query = []
        for kw in args.query:
            kw_type = 'term'
            if kw.startswith('$'):
                kw = kw.strip('$')
                kw_type = 'tex'
            query.append({
                'keyword': kw,
                'type': kw_type
            })

        # actually run query
        results = searcher.search(query,
            verbose=verbose,
            topk=topk,
            trec_output=trec_output
            # TREC line format: _QRY_ID_ docID url rank score runID
        )

        # handle results
        if results['ret_code'] == 0: # successful
            hits = results['hits']
        else:
            print(results['ret_str'])
            exit(1)

        for hit in hits:
            print(hit)

    elif args.docid:
        url, contents = searcher.doc(args.docid)
        print(f'--- doc#{args.docid} ---')
        print(url)
        print(contents)

    elif args.eval_math_collection:
        # preparing evaluation (determine temp file, trec_output etc.)
        if os.path.exists(trec_output):
            print(f'Truncating TREC output file {trec_output}...')
            open(trec_output, 'w').close() # truncate the file

        if not trec_output_specified:
            print('Error: Must specify a TREC output file in evaluation')
            exit(1)

        tmpout = tempfile.mktemp(".trec")
        collection = args.eval_math_collection

        # generate run file from specifed topics
        for qid, query in gen_topics_queries(collection):
            print('[ evaluate ]', qid, query)

            # actually run query
            results = searcher.search(query,
                verbose=verbose,
                topk=topk,
                trec_output=tmpout
                # TREC line format: _QRY_ID_ docID url rank score runID
            )

            ret_code = results['ret_code']
            ret_msg = results['ret_str']
            n_hits = len(results['hits']) if ret_code == 0 else 0
            print(f'[ results ] {ret_msg}(#{ret_code}): {n_hits} hit(s)')

            # inject query ID and append temp file to trec_output file
            with open(tmpout, 'r') as temp_fh:
                temp_contents = temp_fh.read()
                temp_contents = temp_contents.replace('_QRY_ID_', qid)
                with open(trec_output, 'a') as output_fh:
                    output_fh.write(temp_contents)

        # now invoke trec_eval ...
        qrels = get_qrels_filepath(collection)
        eval_output = trec_eval(qrels, trec_output, args.eval_args)
        print('\n --- trec_eval output ---\n' + eval_output, end='')

    else:
        print('no docid, query or evaluating collection specifed, abort.')
        exit(0)
