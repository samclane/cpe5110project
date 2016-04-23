#!/usr/bin/python

import sys, re

#sys.argv is command line args



class Instruction():
	def __init__(self, opcode, argv):
		self.operands = []
		self.opcode = opcode
		for operand in argv:
			self.operands.append(operand.strip(',#'))
		if self.opcode[0] == 'B':
			self.type = "BRANCH"
		elif self.opcode[:2] == "FP":
			self.type = "FLOATING_POINT"
		else:
			self.type = "INTEGER"

	def get_opcode(self):
		return self.opcode

	def get_operands(self):
		return self.operands

	def get_type(self):
		return self.type

	def __str__(self):
		return self.opcode + " " + ' '.join(self.operands)





def main(argv):
	instr_count = -1
	mem_count = -1
	instr_list = []
	mem_dict = {}
	#regular expression describing memory format
	mem_finder = re.compile(ur'<(\d*)> ?<(\d*).?\d*>') 
	print "Welcome to the program"
	if len(argv) != 1: #highly robust input sanitization
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
			elif line[0] is '<': #must be a memory thing
				address, value = re.findall(mem_finder, line)[0]
				mem_dict[address] = value
			

	print "instr_count: " + instr_count
	print "mem_count: " + mem_count
	for instruction in instr_list:
		print str(instruction)
	for address, value in mem_dict.items():
		print "<"+address+">"+"<"+value+">"

if __name__ == "__main__":
	main(sys.argv[1:])

