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
	TRECEVAL=./tools/eval/trec_eval.9.0.4/trec_eval
	QREL=$1
	RUN=$2
	tot_judged=0
	tot_hits=0
	TMPFILE=$(mktemp)

	$TRECEVAL $QREL $RUN -qn -J -m ndcg | sort -k 3,3 > $TMPFILE

	while read line; do
		qry=$(echo $line | awk '{print $2}')
		score=$(echo $line | awk '{print $3}')
		hits=$(cat $RUN | grep "^$qry\b" | wc -l)
		docs=$(cat $RUN | grep "^$qry\b" | awk '{print $3}')
		judged=$(get_num_judged "$docs" $QREL)
		echo $qry $judged/$hits $score
		let "tot_judged+=$judged"
		let "tot_hits+=$hits"
	done < $TMPFILE
	echo "tot_judged=$tot_judged"
	echo "tot_hits=$tot_hits"
}

topic_judged_rate_order_by_score ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./MathDowsers-task1-alpha05noReRank-auto-both-A.tsv | tee mdowsers-best.txt

topic_judged_rate_order_by_score ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./MathDowsers-task1-alpha05translated-manual-both-A.tsv | tee mdowsers-manual.txt

topic_judged_rate_order_by_score ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./Approach0.tsv | tee a0-base.txt

topic_judged_rate_order_by_score ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt ./runs/arqmath-2020-task1-K1000.run | tee pya0.txt

