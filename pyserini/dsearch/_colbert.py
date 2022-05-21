import os
import re
import sys
import pickle
import torch
import faiss
import json
import time
import argparse
import itertools
import statistics
from tqdm import tqdm
from typing import List
from collections import defaultdict
from pyserini.dsearch import DenseSearchResult, QueryEncoder
from pyserini.encode import ColBertEncoder


class ColBertSearcher:
    def __init__(self, index_path: str, query_encoder: QueryEncoder,
                 device='cuda:0', search_range=None, debug_ext_docid=None):
        self.index_path = index_path
        self.encoder = query_encoder
        self.pos2docid = None
        self.device = device

        # time deltas
        self.time_deltas = defaultdict(list)

        if search_range is None:
            div, div_selection = 1, slice(None)
        else:
            assert isinstance(search_range, list)
            assert len(search_range) == 3
            div = search_range[0]
            assert div >= 1
            div_selection = slice(*search_range[1:])

        print('Reading FAISS index...')
        path = os.path.join(self.index_path, 'word_emb.faiss')
        self.faiss_index = faiss.read_index(path)
        self.dim = self.faiss_index.d
        if hasattr(self.faiss_index, 'code_size'):
            self.code_sz = self.faiss_index.code_size
        else:
            # Flat index may not have code_size
            self.code_sz = 16
        self.n_embs = self.faiss_index.ntotal
        print(f'dim={self.dim}, code_sz={self.code_sz}')
        print(f'Total embedding vectors: {self.n_embs:,}')

        print('Reading docIDs...')
        self.ext_docIDs = []
        for _, ext_docID, shard in self.items_of_shards(r'doc_ids\.\d+\.pkl'):
            self.ext_docIDs.append(ext_docID)
        self.n_shards = shard + 1

        print('Generating in-memory offset index...')
        self.pos2docid = torch.zeros(self.n_embs, dtype=torch.long)
        self.doc_lens = []
        self.doc_offsets = []
        self.shard_lens = [0] * self.n_shards
        self.shard_offsets = None
        pos = 0
        for docid, dlen, shard in self.items_of_shards(r'doc_len\.\d+\.pkl'):
            self.pos2docid[pos : pos + dlen] = docid
            self.doc_lens.append(dlen)
            self.doc_offsets.append(pos)
            self.shard_lens[shard] += dlen
            pos += dlen
        self.shard_offsets = list(itertools.accumulate(self.shard_lens))
        self.shard_offsets = [0] + self.shard_offsets[0:-1]
        self.max_doc_len = max(self.doc_lens)
        self.n_docs = docid + 1

        # sanity checks
        assert len(self.ext_docIDs) == self.n_docs
        assert pos == self.n_embs
        assert len(self.doc_lens) == self.n_docs
        assert len(self.doc_offsets) == self.n_docs
        assert sum(self.doc_lens) == self.n_embs
        assert self.shard_offsets[-1] + self.shard_lens[-1] == self.n_embs
        assert self.doc_offsets[-1] + self.doc_lens[-1] == self.n_embs
        print(f'Total documents: {self.n_docs:,}')

        # big tensor memory preloading
        self.doc_offsets = torch.tensor(self.doc_offsets)
        self.doc_lens = torch.tensor(self.doc_lens)
        self.all_div_offsets = self.get_div_offsets(self.doc_offsets, div)
        self.div_offsets = self.all_div_offsets[div_selection]

        # setup debug docid
        self.debug_docid = None
        if debug_ext_docid:
            print('*** DEBUG ***')
            print(f'Looking for {debug_ext_docid} ...')
            # find out debug internal docid
            for j, ext_docid in enumerate(self.ext_docIDs):
                if ext_docid == debug_ext_docid:
                    self.debug_docid =j
                    break
            assert self.debug_docid is not None
            print(f'internal docid = {self.debug_docid}')
            print(f'debug doc len = {self.doc_lens[self.debug_docid]}')
            # find out which division debug docID is
            for i, (low, high) in enumerate(self.all_div_offsets):
                low_docid = self.pos2docid[low]
                high_docid = self.pos2docid[high - 1]
                low_ext_docid = self.ext_docIDs[low_docid]
                high_ext_docid = self.ext_docIDs[high_docid]
                print(f'{i} {i+1}: offset {low}-{high}'
                    + f' => doc {low_docid}-{high_docid}'
                    + f' => ext docID {low_ext_docid}-{high_ext_docid}')
                if self.debug_docid <= high_docid:
                    print(f'doc# {self.debug_docid} @ {div} {i} {i+1}')
                    break

        low, high = self.div_offsets[0][0], self.div_offsets[-1][-1]
        print(f'Loading flat tensors ranged from [{low:,}:{high:,}]')
        self.word_embs = self.get_partial_embs(low, high + self.max_doc_len)

        mem_usage = sys.getsizeof(self.word_embs.storage()) // (1024*1024)
        print(f'Flat tensor memory usage = {mem_usage:,} MiB')

    def items_of_shards(self, pattern, fmt='pickle'):
        def load_pickle_items(path):
            with open(path, 'rb') as fh:
                return pickle.load(fh)
        def load_torch_items(path):
            return torch.load(path)
        cnt = 0
        iterator = tqdm(self.get_sorted_shards_list(pattern))
        for i, filename in enumerate(iterator):
            path = os.path.join(self.index_path, filename)
            if fmt == 'pickle':
                items = load_pickle_items(path)
            elif fmt == 'torch':
                items = load_torch_items(path)
            else:
                raise NotImplementedError
            for item in items:
                yield cnt, item, i
                cnt += 1

    def get_sorted_shards_list(self, regex):
        pattern = re.compile(regex)
        files = os.listdir(self.index_path)
        files = list(filter(lambda x: pattern.match(x), files))
        return sorted(files, key=lambda x: int(x.split('.')[1]))

    def get_partial_embs(self, low, high):
        assert low < high and high <= self.n_embs + self.max_doc_len
        embs = torch.zeros(high - low, self.dim, dtype=torch.float16)
        fill_offset = 0
        embs_files = r'word_emb\.\d+\.pt'
        iterator = tqdm(self.get_sorted_shards_list(embs_files))
        for i, filename in enumerate(iterator):
            offset = self.shard_offsets[i]
            length = self.shard_lens[i]
            shd_int = (offset, offset + length) # shard interval
            sel_int = (low, high) # selection interval
            if shd_int[1] <= sel_int[0]:
                continue
            elif shd_int[0] >= sel_int[1]:
                break
            assert shd_int[0] <= sel_int[0] + fill_offset
            path = os.path.join(self.index_path, filename)
            shard_embs = torch.load(path)
            # load read shard to memory buffer (embs)
            shard_l = sel_int[0] + fill_offset - shd_int[0]
            shard_r = min(shd_int[1], sel_int[1]) - shd_int[0]
            fill_end = fill_offset + (shard_r - shard_l)
            embs[fill_offset:fill_end] = shard_embs[shard_l:shard_r]
            fill_offset = fill_end
        return embs

    def _create_view(self, embs, stride):
        # Example
        # tensor([[ 1.8278, -1.8511],
        #         [ 1.2551,  1.7123],
        #         [-0.4915,  0.6947],
        #         [ 2.3282,  1.8772]])
        #
        # dim = tensor.size(1)
        # stride = 2 # group size
        # outdim = tensor.size(0) - stride + 1 # which equals to 3
        # view = torch.as_strided(tensor, (outdim, stride, dim), (dim, dim, 1))
        #
        # tensor([[[ 1.8278, -1.8511],
        #          [ 1.2551,  1.7123]],
        #         [[ 1.2551,  1.7123],
        #          [-0.4915,  0.6947]],
        #         [[-0.4915,  0.6947],
        #          [ 2.3282,  1.8772]]])
        outdim = embs.size(0) - stride + 1
        return torch.as_strided(embs,
            (outdim, stride, self.dim),
            (self.dim, self.dim, 1)
        )

    def get_div_offsets(self, doc_offsets, div):
        n = doc_offsets.shape[0]
        step = (n // div) + 1
        div_offsets = []
        for low_k in range(0, n, step):
            high_k = min(low_k + step, n - 1)
            low = doc_offsets[low_k].item()
            high = doc_offsets[high_k].item()
            if high_k == n - 1:
                high = self.n_embs
            div_offsets.append((low, high))
        return div_offsets

    def colbert_rank(self, qcode, uniq_docids):
        start = time.time()
        # prepare query and document tensors
        Q = qcode.permute(0, 2, 1).to(self.device) # [qnum, dim, max_qlen]
        Q = Q.to(dtype=torch.float16) # float16

        # shortcut variables
        lowest = self.div_offsets[0][0] # lowest offset in self.word_embs
        stride = self.max_doc_len

        # tensorize candidate docIDs
        all_scores = torch.zeros(len(uniq_docids), device=self.device)
        uniq_docids = torch.tensor(uniq_docids, device=self.device)

        # filter candidates for compuation efficiency
        doc_offsets = self.doc_offsets[uniq_docids]
        doc_lens = self.doc_lens[uniq_docids]

        self.time_deltas['prepare_rank'].append(time.time() - start)

        # split search into segments
        for low, high in self.div_offsets:
            # select documents in this division
            start = time.time()
            in_range = torch.logical_and(
                low <= doc_offsets, doc_offsets < high
            )
            div_doc_offsets = doc_offsets[in_range]
            n_div_cands = div_doc_offsets.shape[0]
            if n_div_cands == 0:
                continue
            div_doc_lens = doc_lens[in_range]
            div_uniq_docids = uniq_docids[in_range]

            # selecting word embeddings in this division
            print(f'Loading embs offset [{low:,}:{high:,}]', end=" ")
            word_embs = self.word_embs[low - lowest : high + stride - lowest]
            view = self._create_view(word_embs, stride)
            select_idx = div_doc_offsets - low
            div_cands = torch.index_select(view, 0, select_idx)
            print('candidates:', div_cands.shape[0])
            self.time_deltas['select_embs'].append(time.time() - start)

            start = time.time()
            div_cands = div_cands.to(self.device) # move to device
            assert div_cands.shape == (n_div_cands, stride, self.dim)
            self.time_deltas['load2gpu'].append(time.time() - start)

            start = time.time()
            # create mask tensor for filtering out doc padding words
            mask = torch.arange(stride) # doc word offsets
            mask = (mask.unsqueeze(0) < div_doc_lens.unsqueeze(-1))
            mask = mask.to(self.device)
            assert mask.shape == (n_div_cands, stride)

            # apply ColBert scoring function
            scores = div_cands @ Q # [cands, stride, dim] @ [qnum, dim, qlen]
            scores = scores * mask.unsqueeze(-1) # [n_cands, stride, qlen]
            scores = scores.float() # convert to full precision for max()
            all_scores[in_range] = scores.max(1).values.sum(-1) # scoring

            self.time_deltas['gpu_compute'].append(time.time() - start)

            # release in-loop temp memory
            start = time.time()
            del div_cands
            del view
            del word_embs
            torch.cuda.empty_cache()
            self.time_deltas['release'].append(time.time() - start)

            # debug embedding
            if self.debug_docid is not None:
                ext_docID = self.ext_docIDs[self.debug_docid]
                scores = scores.cpu()
                torch.save(scores, f'debug-scores-{ext_docID}.pt')
                #import pdb
                #pdb.set_trace()

        return all_scores.cpu().tolist()

    def report(self, report_filename='colbert_time_report.txt'):
        report = defaultdict(dict)
        for key in self.time_deltas:
            runtimes = self.time_deltas[key]
            output = report[key]
            output['avg'] = statistics.mean(runtimes)
            output['med'] = statistics.median(runtimes)
            output['max'] = max(runtimes)
            output['min'] = min(runtimes)
            output['len'] = len(runtimes)
            if len(runtimes) >= 2:
                output['std'] = statistics.stdev(runtimes)
            for key in output:
                output[key] = round(output[key], 3) # to milli-seconds
        print('ColBertSearcher report:', report)
        output_json = json.dumps(report, sort_keys=True, indent=4)
        with open(report_filename, 'w') as fh:
            fh.write(output_json)
            fh.write('\n')

    def search(self, query: str, k: int = 10) \
        -> List[DenseSearchResult]:
        # encode query
        qcode, _ = self.encoder.encode([query],
            fp16=(self.code_sz==16), debug=False)

        return self.search_code(qcode, k)

    def search_code(self, qcode, k):
        qnum, max_qlen, dim = qcode.shape
        assert dim == self.dim
        assert qnum == 1

        start = time.time()
        # retrieve candidates per keyword
        if self.debug_docid is not None:
            uniq_docids = [[self.debug_docid]]
        else:
            Q = qcode.view(-1, dim).cpu().contiguous() # [qnum * max_qlen, dim]
            cand_depth = max(1024, k)
            _, QD_embpos = self.faiss_index.search(Q.numpy(), cand_depth)
            QD_embpos = torch.tensor(QD_embpos).view(qnum, -1)
            QD_docids = self.pos2docid[QD_embpos] # [qnum, max_qlen*cand_depth]
            # rank candidates
            uniq_docids = list(map(lambda x: list(set(x)), QD_docids.tolist()))
        self.time_deltas['faiss'].append(time.time() - start)

        # rank candidates with colbert scoring
        start = time.time()
        scores = self.colbert_rank(qcode, uniq_docids[0])
        self.time_deltas['rerank'].append(time.time() - start)

        # sort results
        start = time.time()
        results = zip(uniq_docids[0], scores)
        results = sorted(results, key=lambda x: x[1], reverse=True)
        results = results[:k] # only extract top-K results
        results = [
            DenseSearchResult(self.ext_docIDs[i], score)
            for i, score in results
            if score != 0
        ]
        self.time_deltas['sort'].append(time.time() - start)
        return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ColBertSearcher Test.')
    parser.add_argument('--device', type=str, default='cpu',
        help='Device to run query encoder and searcher.')
    parser.add_argument('--query', type=str, required=True,
        help="Test query in string.")
    parser.add_argument('--encoder', type=str, required=True,
        help="Path or name for ColBert query encoder.")
    parser.add_argument('--tokenizer', type=str, required=True,
        help="Path or name for ColBert query tokenizer.")
    parser.add_argument('--index', type=str, required=True,
        help="Path to ColBert index directory.")
    parser.add_argument('--topk', type=int, default=10,
        help="Limit the number of maximum top-k results.")
    parser.add_argument('--div', type=int, default=1,
        help="Total number of divisions, each will moved to search device.")
    parser.add_argument('--div-selection', type=int, nargs="+",
        help="Divisions selected for search (relevant tensors will be cached).")
    parser.add_argument('--docid', type=str,
        help="Print out document tensor for specific docID (debug purpose).")
    args = parser.parse_args()

    print('#divisions:', args.div)
    print('selection:', args.div_selection)

    encoder = ColBertEncoder(args.encoder, '[Q]',
        device=args.device, tokenizer=args.tokenizer, query_augment=True)

    if args.div_selection is None:
        search_range = None
    else:
        search_range = [args.div, *args.div_selection]
    searcher = ColBertSearcher(args.index, encoder, device=args.device,
        search_range=search_range, debug_ext_docid=args.docid)

    print('[test query]', args.query)
    results = searcher.search(args.query, k=args.topk)
    for rank, hit in enumerate(results):
        print(rank + 1, hit.docid, '\t', hit.score)
