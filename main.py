#!/usr/bin/python

import sys, re


# sys.argv is command line args


class Instruction():
    def __init__(self, opcode, argv):
        self.operands = []
        self.opcode = opcode
        for operand in argv:
            self.operands.append(operand.strip(',#'))
        if self.opcode[0] == 'B':
            self.type = "BRANCH"
        elif self.opcode == "FPMULT" or self.opcode == "FPDIV":
            self.type = "FPMULT"
        elif self.opcode == "FPADD" or self.opcode == "FPSUB":
            self.type = "FPADD"
        elif self.opcode == "MOV" or self.opcode == "LOAD" or self.opcode == "STR":
            self.type = "MEMORY_ACCESS"
        else:
            self.type = "INT"

    def get_opcode(self):
        return self.opcode

    def get_operands(self):
        return self.operands

    def get_type(self):
        return self.type

    def __str__(self):
        # defines the print() function for Instruction
        return self.opcode + " " + ' '.join(self.operands)


class RegisterFile(dict):
    def __init__(self, *args, **kwargs):
        super(RegisterFile, self).__init__(*args, **kwargs)
        self.itemlist = super(RegisterFile, self).keys()

    def __setitem__(self, key, value):
        self.itemlist.append(key)
        super(RegisterFile, self).__setitem__(key, value)

    def __iter__(self):
        return iter(self.itemlist)

    def keys(self):
        return self.itemlist

    def values(self):
        return [self[key] for key in self]

    def itervalues(self):
        return (self[key] for key in self)


class ReservationStation():
    def __init__(self, size, op_type):
        self.size = size
        self.op_type = op_type
        self.entry_list = []
        for x in xrange(self.size):
            self.entry_list.append((False, '', False, '', False, False))

    def load_instruction(self, instruction):
        for idx, entry in enumerate(self.entry_list):
            if entry[0] is False:
                self.entry_list[idx] = (
                True, instruction.get_operands()[0], False, instruction.get_operands()[1], False, False)
                return True
        return False

    def __str__(self):
        return str(self.entry_list)


def issue(instruction):
    global rs_int, rs_fp_add, rs_fp_mult, PC
    succeeds = False
    if instruction.get_type() == "BRANCH" or instruction.get_type() == "INT":
        succeeds = rs_int.load_instruction(instruction)
    elif instruction.get_type() == "FPADD":
        succeeds = rs_fp_add.load_instruction(instruction)
    elif instruction.get_type() == "FPMULT":
        succeeds = rs_fp_mult.load_instruction(instruction)
    if succeeds == True:
        PC = PC + 1


ZERO, NEGATIVE, OVERFLOW = (False, False, False)
OUT_OF_ORDER = False
instr_count = -1
mem_count = -1
instr_queue = []
mem_dict = {}
R = RegisterFile()
rs_fp_add = ReservationStation(3, 'FPADD')
rs_fp_mult = ReservationStation(2, 'FPMULT')
rs_int = ReservationStation(2, 'INT')
load_buffer = {}
rob = {}
PC = 0


def main(argv):
    # Global System Flags
    global instr_count, mem_count, instr_queue, mem_dict
    # regular expression describing memory format
    # https://regex101.com/r/zY4hB0/3
    mem_finder = re.compile(ur'<(\d+)> ?<([-+]?\d*\.?\d*)>')
    print "Welcome to the program"
    if len(argv) != 1:  # highly robust input sanitization
        print "Wrong number of files!"
        return
    with open(argv[0]) as codefile:
        for line in codefile:
            line = line.partition('--')[0]
            if len(line) == 0:  # if trimmed line is empty, go to next iteration
                continue
            if line[0].isdigit():  # must be a count
                if instr_count == -1:
                    instr_count = line
                elif mem_count == -1:
                    mem_count = line
            elif line[0].isalpha():  # must be an instruction
                if line[0] == 'H':
                    continue
                opcode = line.split()[0]
                operands = line.split()[1:]
                instr = Instruction(opcode, operands)
                instr_queue.append(instr)
            elif line[0] is '<':  # must be a memory thing
                address, value = re.findall(mem_finder, line)[0]
                mem_dict[address] = value

    for instruction in instr_queue:
        print "issuing " + str(instruction)
        issue(instruction)
        print rs_int
        print rs_fp_add
        print rs_fp_mult
        print "\n"

    print "instr_count: " + instr_count
    print "mem_count: " + mem_count
    for instruction in instr_queue:
        print str(instruction)
        print " " + instruction.get_type();
    for address, value in mem_dict.items():
        print "<" + address + ">" + "<" + value + ">"


# magic code than runs main
if __name__ == "__main__":
    main(sys.argv[1:])
