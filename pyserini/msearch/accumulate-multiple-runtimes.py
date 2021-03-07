#!/usr/bin/python3
import sys
import json
import numpy

name = sys.argv[1] if len(sys.argv) > 1 else 'arqmath-2020-task1'
accum = None

for i in range(5):
	run_num = i + 1
	path = f'runs/{name}.{run_num}.runtimes'
	with open(path, 'r') as fh:
		j = json.load(fh)
		runtimes = numpy.array(j['runtimes'])
		if accum is None:
			accum = numpy.zeros(runtimes.shape)
		accum += runtimes

accum /= 5
print(','.join(map(str, accum.tolist())))
