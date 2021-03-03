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
python3 -m pyserini.msearch --index arqmath-2020-task1 --eval-math-topics arqmath-2020-task1 --topk 1000 --trec-output arqmath-2020-task1.run --eval-args '-l 3'
```
(here `-l 3` will be passed to `trec_eval` to generate evaluation with scores of 3 or higher considered relevant)

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
