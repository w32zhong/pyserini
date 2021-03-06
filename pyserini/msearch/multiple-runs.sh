#!/bin/bash

NAME=arqmath-2020-task1

INDEX=$NAME
TOPICS=$NAME
RUN=$NAME

single_run() {
	num=${1-1}
	python3 -m pyserini.msearch --index $INDEX --topk 1000 --eval-math-topics $TOPICS --trec-output ./runs/$RUN.run --verbose > ./runs/$RUN.$num.output
	runtimes=$(cat ./runs/$RUN.$num.output | ./pyserini/msearch/collect-runtimes.sh)
	python3 ./pyserini/msearch/calc-runtime-stats.py $runtimes > ./runs/$RUN.$num.runtimes
}

#for i in {1..5}; do single_run $i; done
overall_runtimes=$(python3 pyserini/msearch/calc-multiple-runtimes-stats.py)
python3 ./pyserini/msearch/calc-runtime-stats.py $overall_runtimes > ./runs/$RUN.overall.runtimes
