#!/usr/bin/python3
import sys
import json
import numpy

name = 'arqmath-2020-task1'
accum = numpy.zeros(98)

for i in range(5):
	run_num = i + 1
	path = f'runs/{name}.{run_num}.runtimes'
	with open(path, 'r') as fh:
		j = json.load(fh)
		runtimes = numpy.array(j['runtimes'])
		accum += runtimes
		#print(runtimes.shape)

accum /= 5
print(','.join(map(str, accum.tolist())))
