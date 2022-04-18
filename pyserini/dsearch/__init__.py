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

#from ._dsearcher import DenseSearchResult, PRFDenseSearchResult, SimpleDenseSearcher, BinaryDenseSearcher, QueryEncoder, \
#    DprQueryEncoder, BprQueryEncoder, DkrrDprQueryEncoder, TctColBertQueryEncoder, AnceQueryEncoder, AutoQueryEncoder
from ._dsearcher import DenseSearchResult, QueryEncoder
from ._colbert import ColBertSearcher
#from ._model import AnceEncoder
#from ._prf import DenseVectorAveragePrf, DenseVectorRocchioPrf, DenseVectorAncePrf

#__all__ = ['DenseSearchResult', 'PRFDenseSearchResult', 'SimpleDenseSearcher', 'BinaryDenseSearcher', 'ColBertSearcher',
#    'QueryEncoder', 'DprQueryEncoder', 'BprQueryEncoder', 'DkrrDprQueryEncoder', 'TctColBertQueryEncoder', 'AnceEncoder',
#           'AnceQueryEncoder', 'AutoQueryEncoder', 'DenseVectorAveragePrf', 'DenseVectorRocchioPrf', 'DenseVectorAncePrf']
