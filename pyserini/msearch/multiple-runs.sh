#!/bin/bash

set -ex
NAME=${1-"arqmath-2020-task1"}
TOPICS=${2-$NAME}
K=${3-1000}

INDEX=$NAME
RUN="$NAME-K${K}"

single_run() {
	num=${1-1}
	python3 -m pyserini.msearch --index $INDEX --topk $K --eval-math-topics $TOPICS --trec-output ./runs/$RUN.run --verbose > ./runs/$RUN.$num.output
	runtimes=$(cat ./runs/$RUN.$num.output | ./pyserini/msearch/collect-runtimes.sh)
	python3 ./pyserini/msearch/calc-runtime-stats.py $runtimes > ./runs/$RUN.$num.runtimes
}

for i in {1..5}; do
	echo "run#${i}...";
	single_run $i;
done
overall_runtimes=$(python3 pyserini/msearch/accumulate-multiple-runtimes.py $RUN)
python3 ./pyserini/msearch/calc-runtime-stats.py $overall_runtimes > ./runs/$RUN.overall.runtimes
set +ex
