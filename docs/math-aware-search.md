# Math-Aware Search
Math-aware search is the ability to add math expression(s) as some of your keywords to have search engine help you find similar expressions and return those documents/topics that you may find relevant to your query. In short, a typical search engine plus math search.

This fork of Pysernini provides the ability to search math by using a Python interface on math-aware search engine [Approach Zero](https://github.com/approach0/search-engine).

## Installation
STEP 1:

Prepare math-aware fork of Pysernini:
```sh
sudo pip3 install tqdm pandas pya0
git clone https://github.com/t-k-/pyserini
cd pyserini
git clone https://github.com/t-k-/anserini-tools
rm -rf tools && mv anserini-tools tools
cd tools/eval && tar xvfz trec_eval.9.0.4.tar.gz && cd trec_eval.9.0.4 && make && cd ../../..
```

STEP 2: (optional unless you need to bind Lucene using PyJNIus)

Prepare dependencies and build Ansernini:
```sh
cd ..
sudo apt install -y openjdk-11-jdk openjdk-11-jre maven
git clone https://github.com/castorini/anserini.git
cd anserini
export JAVA_HOME=$(update-alternatives --query javadoc | grep Value: | head -n1 | sed 's/Value: //' | sed 's@bin/javadoc$@@') # assume it is a Debian-like system (such as Ubuntu)
mvn clean package appassembler:assemble
cp target/anserini-0.11.1-SNAPSHOT-fatjar.jar ../pyserini/pyserini/resources/jars/
cd ../pyserini
```

STEP 3: (test installation)

Download and play with a toy index to test installation:
```
python3 -m pyserini.msearch --index tiny-mse --query 'proof' --verbose
```
(this will download a toy pre-built index with data from Math StackExchange, stored in Python cache directory at `~/.cache/pyserini/indexes/`)

## Usages
`pyserini.msearch` module is the main enter point for math-aware search functionalities.

To list available pre-built math indexes:
```
python3 -m pyserini.msearch --list-prebuilt-indexes
```

There are a few math collection query topics (with judgement pool) available:
```
ls tools/topics-and-qrels/topics.arqmath*
ls tools/topics-and-qrels/topics.ntcir12-math-browsing*
```

To download a pre-built index and perform evaluation given `arqmath-2020-task1` as example:
```
python3 -m pyserini.msearch --index arqmath-2020-task1 --eval-math-topics arqmath-2020-task1 --topk 1000 --trec-output arqmath-2020-task1.run --eval-args '-l 2 -J -m map -m P.10'
```
(here `-l 2 -J -m map -m P.10` will be passed to `trec_eval` to generate evaluation with scores of 2 or higher considered relevant and it reports results using the MAP and P@10 metrics over only the judged hits)

Alternatively, after a run file is generated, we can directly invoke `trec_eval` to generate evaluation metrics:
```
/tools/eval/trec_eval.9.0.4/trec_eval ./tools/topics-and-qrels/qrels.arqmath-2020-task1.txt arqmath-2020-task1.run -J -m ndcg
```

To print index statistics:
```
python3 -m pyserini.msearch --index arqmath-2020-task1 --print-index-stats
```

To query document ID from index:
```
python3 -m pyserini.msearch --index arqmath-2020-task1 --docid 123
```

To manually query math formulas and text keywords (you can mix different type of keywords for math-aware search):
```
python3 -m pyserini.msearch --index arqmath-2020-task1 --query 'prove' --query '$a^2 + b^2 = c^2$'
```

## Generate query runtimes
Query runtimes is measured in the core engine code in order to generate accurate runtimes that do not include Python layer noises.

The way to get these numbers is to collect standard output under `verbose` mode and use an utility script `collect-runtimes.sh`. Then use another script `./pyserini/msearch/calc-runtime-stats.py` to generate runtime statistics:
```
$ python3 -m pyserini.msearch --index arqmath-2020-task1 --eval-math-topics arqmath-2020-task1 --topk 1000 --trec-output arqmath-2020-task1.run --verbose > arqmath-2020-task1.output

$ cat arqmath-2020-task1.output | ./pyserini/msearch/collect-runtimes.sh
775,364,8,3543,756,494,838,526,738,1059,3241,1367,801,2437,1240,1214,2056,1254,813,416,43,1790,418,181,986,1809,2175,388,50,833,885,266,20,131,540,306,8,615,1216,709,643,1701,28,1065,1410,562,650,1086,2153,780,3849,564,573,365,661,568,1335,1818,1879,580,230,2315,325,861,908,229,840,417,2003,3006,748,1116,514,1626,2035,361,3498,1002,30,26,980,757,1139,1650,1474,1331,260,803,52,1208,314,532,16,1185,124,5692,647,

$ python3 ./pyserini/msearch/calc-runtime-stats.py 775,364,8,3543,756,494,838,526,738,1059,3241,1367,801,2437,1240,1214,2056,1254,813,416,43,1790,418,181,986,1809,2175,388,50,833,885,266,20,131,540,306,8,615,1216,709,643,1701,28,1065,1410,562,650,1086,2153,780,3849,564,573,365,661,568,1335,1818,1879,580,230,2315,325,861,908,229,840,417,2003,3006,748,1116,514,1626,2035,361,3498,1002,30,26,980,757,1139,1650,1474,1331,260,803,52,1208,314,532,16,1185,124,5692,647, > arqmath-2020-task1.runtimes
```

## Automatic Script
Run `pyserini/msearch/multiple-runs.sh` to generate topic run files under `./runs` directory. Runtimes are averaged over 5 multiple runs.
