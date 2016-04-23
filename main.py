#!/usr/bin/python

import sys, getopt

#sys.argv is command line args




class Instruction():
	def __init__(self, opcode, argv):
		self.operands = []
		self.opcode = opcode
		for operand in argv:
			self.operands.append(operand.strip(','))

	def get_opcode(self):
		return self.opcode

	def get_operands(self):
		return self.operands


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
				opcode = line.split()[0]
				operands = line.split()[1:]
				instr = Instruction(opcode,operands)
				instr_list.append(instr)
			else: #must be a memory thing
				mem_list.append(line)
	print "instr_count: " + instr_count
	print "mem_count: " + mem_count
	print instr_list
	print mem_list
	for instruction in instr_list:
		print "Opcode: " + instruction.get_opcode()
		for idx, operand in enumerate(instruction.get_operands()):
			print "Operand " + str(idx) + ": " + operand

if __name__ == "__main__":
	main(sys.argv[1:])

