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
"""
This module provides Pyserini's math-aware search ability from Approach0
"""
import json
from typing import List, Dict, Tuple
from pyserini.util import get_math_indexes_info, download_prebuilt_index
from pya0 import index_open as math_index_open
from pya0 import search as math_search
from pya0 import index_lookup_doc as math_raw_doc
from pya0 import index_print_summary


class MathSearcher:
    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.index = math_index_open(index_dir, option="r")

    @classmethod
    def from_prebuilt_index(cls, prebuilt_index_name: str):
        print(f'Attempting to initialize pre-built index {prebuilt_index_name}.')
        try:
            index_dir = download_prebuilt_index(prebuilt_index_name)
        except ValueError as e:
            print(str(e))
            return None

        print(f'Initializing {prebuilt_index_name}...')
        return cls(index_dir)

    @staticmethod
    def list_prebuilt_indexes():
        get_math_indexes_info()

    def print_index_stats(self):
        index_print_summary(self.index)

    def search(self, q: List[Dict[str, str]], k: int = 10, verbose: bool = False, topk: int = 20, trec_output: str = None) -> str:
        JSON_str = math_search(self.index, q, verbose=verbose, topk=topk, trec_output=trec_output)
        hits = json.loads(JSON_str)
        return hits

    def doc(self, docid: int) -> Tuple[str, str]:
        return math_raw_doc(self.index, docid)
