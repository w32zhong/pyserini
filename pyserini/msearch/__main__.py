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

from pyserini.msearch import MathSearcher


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Conduct math-aware search using Approach0 search engine')

    parser.add_argument('--query', type=str, required=True, nargs='+',
        help="Mixed type of keywords, math keywords are written in TeX and wrapped up in dollars")
    parser.add_argument('--index-path', type=str, required=True,
        help="Open index at specified path")
    parser.add_argument('--topk', type=int, required=False,
        help="Keep at most top-K hits in results")
    parser.add_argument('--trec-output', type=str, required=False,
        help="Output TREC-format results")
    parser.add_argument('--verbose', required=False, action='store_true',
        help="Verbose output (showing query structures and merge times)")

    args = parser.parse_args()
    #print(args)

    # create searcher from specified index path
#ssearcher = SimpleSearcher.from_prebuilt_index(args.sparse.index)
    if not os.path.exists(args.index_path):
        print(f'Error: Path {args.index_path} does not exist.')
        exit(1)

    searcher = MathSearcher(args.index_path)

    # parser queries by different types
    queries = []
    for kw in args.query:
        kw_type = 'term'
        if kw.startswith('$'):
            kw = kw.strip('$')
            kw_type = 'tex'
        queries.append({
            'keyword': kw,
            'type': kw_type
        })

    # overwrite default arguments for running searcher
#print(f'Running {args.run.topics} topics, saving to {output_path}...')
    verbose = args.verbose if args.verbose else False
    topk = args.topk if args.topk else 20
    trec_output = args.trec_output if args.trec_output else '/dev/null'

    # actually run query
    results = searcher.search(queries,
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
