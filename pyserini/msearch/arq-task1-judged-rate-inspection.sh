./tools/eval/trec_eval.9.0.4/trec_eval ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./runs/arqmath-2020-task1-K1000.run -qn -J -m ndcg | sort -k 3,3 > a0-ndcg.txt

./tools/eval/trec_eval.9.0.4/trec_eval ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./MathDowsers-task1-alpha05translated-manual-both-A.tsv -qn -J -m ndcg | sort -k 3,3 > mdowsers-ndcg.txt

get_num_judged() {
	DOCS="$1"
	QREL=$2
	cnt=0
	for doc in $DOCS; do
		if grep "\b$doc\b" $QREL &> /dev/null; then
			let cnt++
		fi
	done
	echo $cnt
}

topic_judged_rate_order_by_score() {
	QREL=$1
	RUN=$2
	INPUT=$3
	tot_judged=0
	tot_hits=0
	while read line; do
		qry=$(echo $line | awk '{print $2}')
		score=$(echo $line | awk '{print $3}')
		hits=$(cat $RUN | grep "^$qry\b" | wc -l)
		docs=$(cat $RUN | grep "^$qry\b" | awk '{print $3}')
		judged=$(get_num_judged "$docs" $QREL)
		echo $qry $judged/$hits $score
		let "tot_judged+=$judged"
		let "tot_hits+=$hits"
	done < $INPUT
	echo "tot_judged=$tot_judged"
	echo "tot_hits=$tot_hits"
}

topic_judged_rate_order_by_score ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./runs/arqmath-2020-task1-K1000.run a0-ndcg.txt

#topic_judged_rate_order_by_score ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./MathDowsers-task1-alpha05translated-manual-both-A.tsv mdowsers-ndcg.txt
