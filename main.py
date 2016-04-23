#!/usr/bin/python

import sys, getopt

#sys.argv is command line args

def main(argv):
	instr_count = -1
	mem_count = -1
	instr_list = []
	mem_list = []
	print "Welcome to the program"
	if len(argv) != 1:
		print "Wrong number of files!"
		return
	with open(argv[0]) as codefile:
		for line in codefile:
			line = line.partition('--')[0]
			if len(line) == 0:
				continue
			print line
			if line[0].isdigit(): #must be a count
				if instr_count == -1:
					instr_count = line
				elif mem_count == -1:
					mem_count = line
			elif line[0].isalpha(): #must be an instruction
				instr_list.append(line)
			else: #must be a memory thing
				mem_list.append(line)
	print "instr_count: " + instr_count
	print "mem_count: " + mem_count
	print instr_list
	print mem_list

if __name__ == "__main__":
	main(sys.argv[1:])

