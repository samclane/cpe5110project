#!/usr/bin/python

import re
import sys


# sys.argv is command line args

class Instruction():
    def __init__(self, opcode, argv):
        self.operands = []
        self.opcode = opcode
        for operand in argv:
            self.operands.append(operand.strip(','))
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


class ReservationEntry():
    def __init__(self, busy=False, op1="", op1valid=False, op2="", op2valid=False, ready=False, rob_index=-1):
        self.busy = busy
        self.op1 = op1
        self.op1valid = op1valid
        self.op2 = op2
        self.op2valid = op2valid
        self.ready = ready
        self.rob_index = rob_index

    def __str__(self):
        return "Busy: %s Operand1: %s Valid: %s Operand2: %s Valid: %s Ready: %s" % (
            self.busy, self.op1, self.op1valid, self.op2, self.op2valid, self.ready)


class ReservationStation():
    def __init__(self, size, op_type):
        self.size = size
        self.op_type = op_type
        self.entry_list = []
        for x in xrange(self.size):
            self.entry_list.append(ReservationEntry(False, '', False, '', False, False))

    def load_instruction(self, instruction, rob_index):
        for idx, entry in enumerate(self.entry_list):
            if entry.busy is False:
                if instruction.type == "BRANCH":
                    self.entry_list[idx] = ReservationEntry(True, instruction.operands[0], False,
                                                            instruction.operands[1], False, False, rob_index)

                else:
                    self.entry_list[idx] = ReservationEntry(
                        True, instruction.operands[1], False, instruction.operands[2], False, False, rob_index)
                return True
        return False

    def __str__(self):
        returnlist = ""
        for entry in self.entry_list:
            returnlist = returnlist + str(entry)
        return returnlist


class LoadBufferEntry():
    def __init__(self, busy=False, destination="", source="", rob_index=-1):
        self.busy = busy
        self.destination = destination
        self.source = source
        self.rob_index = rob_index


class LoadBuffer():
    def __init__(self):
        self.entry_list = []

    def add_entry(self, instruction, rob_index):
        self.entry_list.append(LoadBufferEntry(True, instruction.operands[0], instruction.operands[1], rob_index))

    def get_entry(self, index):
        return self.entry_list[index]

    def __str__(self):
        returnlist = ""
        for entry in self.entry_list:
            returnlist = returnlist + str(entry)
        return returnlist


class ReorderBufferEntry():
    def __init__(self, opcode="", dest="", exe_cycles=1, result="", ready=False, speculative=False):
        self.opcode = opcode
        self.dest = dest
        self.exe_cycles = exe_cycles
        self.result = result
        self.ready = ready
        self.speculative = speculative


class ReorderBuffer():
    def __init__(self):
        self.entry_list = []

    def add_entry(self, instruction):
        self.entry_list.append(
            ReorderBufferEntry(instruction.opcode, instruction.operands[0], cycle_dict[instruction.opcode]))
        return len(self.entry_list) - 1  # index of value added


# Glboal values
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
load_buffer = LoadBuffer()
reorder_buffer = ReorderBuffer()
program_counter = 0
cycle_dict = {
    "FPADD": 3,
    "FPSUB": 3,
    "FPMULT": 5,
    "FPDIV": 8,
    "ADD": 1,
    "SUB": 1,
    "LOAD": 1,
    "MOV": 1,
    "STR": 3,
    "BR": 1,
    "BGT": 1,
    "BLT": 1,
    "BGE": 1,
    "BLE": 1,
    "BZ": 1,
    "BNEZ": 1
}


def main(argv):
    # Global System Flags
    global instr_count, mem_count, instr_queue, mem_dict
    # regular expression describing memory format
    # https://regex101.com/r/zY4hB0/3
    mem_finder = re.compile(ur"<(\d+)> ?<([-+]?\d*\.?\d*)>")
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
                opcode = line.split()[0]
                operands = line.split()[1:]
                instr = Instruction(opcode, operands)
                instr_queue.append(instr)
            elif line[0] is '<':  # must be a memory thing
                address, value = re.findall(mem_finder, line)[0]
                mem_dict[address] = value



    while(instr_queue[program_counter].opcode != "HALT"):
        issue(instr_queue[program_counter])


    print "instr_count: " + instr_count
    print "mem_count: " + mem_count
    for instruction in instr_queue:
        print str(instruction)
        print " " + instruction.type
    for address, value in mem_dict.items():
        print "<" + address + ">" + "<" + value + ">"


def issue(instruction):
    global rs_int, rs_fp_add, rs_fp_mult, program_counter
    succeeds = False
    rob_index = reorder_buffer.add_entry(instruction)
    if instruction.type == "BRANCH" or instruction.type == "INT":
        succeeds = rs_int.load_instruction(instruction, rob_index)
    elif instruction.type == "FPADD":
        succeeds = rs_fp_add.load_instruction(instruction, rob_index)
    elif instruction.type == "FPMULT":
        succeeds = rs_fp_mult.load_instruction(instruction, rob_index)
    elif instruction.type == "MEMORY_ACCESS":
        succeeds = True
        load_buffer.add_entry(instruction, rob_index)
    if succeeds == True or succeeds == False:
        program_counter = program_counter + 1


# magic code than runs main
if __name__ == "__main__":
    main(sys.argv[1:])
