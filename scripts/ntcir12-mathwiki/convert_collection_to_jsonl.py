#
# Pyserini: Reproducible IR research with sparse and dense representations
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
import json
import os
from tqdm import tqdm

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', type=str, help='path of NTCIR12 latex text file', required=True)
    parser.add_argument('--output', type=str, help='output path', required=True)
    args = parser.parse_args()

    corpus = os.path.expanduser(args.corpus)
    output = os.path.expanduser(args.output)

    if not os.path.exists(output):
        os.mkdir(output)

    with open(corpus, 'r') as fh:
        for idx, line in enumerate(tqdm(fh.readlines())):
            line = line.rstrip()
            fields = line.split()
            docid_and_pos = fields[0]
            latex = ' '.join(fields[1:])
            latex = latex.replace('% ', '')
            latex = f'[imath]{latex}[/imath]'
            tokens = preprocess_for_transformer(latex)
            tokens = '[D] ' + tokens
            docids.append((docid_and_pos, latex))
