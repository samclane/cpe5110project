#!/usr/bin/python

import re
import sys


# sys.argv is command line args

class Instruction():
    def __init__(self, opcode, argv):
        operands = []
        self.opcode = opcode
        for operand in argv:
            operands.append(operand.strip(','))
        if opcode in ["FPADD", "FPSUB", "FPMULT", "FPDIV", "ADD", "SUB"]:
            self.destination = operands[0]
            self.source1 = operands[1]
            self.source2 = operands[2]
        elif opcode in ["LOAD", "MOV"]:
            self.destination = operands[0]
            self.source1 = None
            self.source2 = operands[1]
        elif opcode == 'BR':
            self.destination = None
            self.source1 = None
            self.source2 = operands[0]
        elif opcode == 'STR' or opcode[0] == 'B':
            self.destination = None
            self.source1 = operands[0]
            self.source2 = operands[1]
        else:
            self.destination = None
            self.source1 = None
            self.source2 = None

        self.total_cycles = cycle_dict[self.opcode]


class RegisterFile(dict):
    def __init__(self, *args, **kwargs):
        super(RegisterFile, self).__init__(*args, **kwargs)
        self.itemlist = super(RegisterFile, self).keys()
        for x in xrange(16):
            self[x] = 0

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





class ReorderBufferEntry():
    def __init__(self, instruction, clock_cycle, rs_index, rs_type):
        self.opcode = instruction.opcode
        self.destination = instruction.destination
        self.source1 = instruction.source1
        self.source1_ROB = None
        self.source1_valid = True
        self.source2 = instruction.source2
        self.source2_ROB = None
        self.source2_valid = True
        self.total_cycles = instruction.total_cycles
        self.result = ""
        self.speculative = False
        self.remaining_cycles = self.total_cycles
        self.executing = False
        self.ready = False
        self.cycle_issued = clock_cycle
        self.rs_index = rs_index
        self.rs_type = rs_type
        self.write_back_success = False

    def get_values(self):
        value1, value2 = (None, None)
        if self.source1 is not None:
            if self.source1[0] is 'R':
                value1 = R[int(self.source1[1:])]
            elif self.source1[0] is '#':
                value1 = self.source1[1:]
            else:
                value1 = mem_dict[self.source1]
            value1 = float(value1)

        if self.source2 is not None:
            if self.source2[0] is 'R':
                value2 = R[int(self.source2[1:])]
            elif self.source2[0] is '#':
                value2 = self.source2[1:]
            else:
                value2 = mem_dict[self.source2]
            value2 = float(value2)


        return (value1, value2)



class ReorderBuffer():
    def __init__(self):
        self.entry_list = []

    def add_entry(self, instruction, clock_cycle, rs_index, rs_type):
        self.entry_list.append(ReorderBufferEntry(instruction, clock_cycle, rs_index, rs_type))
        return len(self.entry_list) - 1  # index of value added

    def check_destinations(self, value):
        index = -1
        for idx, entry in enumerate(self.entry_list):
            if entry.destination is not None:
                if entry.destination == value and entry.destination[0] != '#':
                    index = idx
        return index

    def check_source1(self, value):
        index = -1
        for idx, entry in enumerate(self.entry_list):
            if entry.source1 is not None:
                if entry.source1 == value and entry.source1[0] != '#':
                    index = idx
        return index


    def check_source2(self, value):
        index = -1
        for idx, entry in enumerate(self.entry_list):
            if entry.source2 is not None:
                if entry.source2 == value and entry.source2[0] != '#':
                    index = idx
        return index



# Glboal values
ZERO, NEGATIVE, OVERFLOW = (False, False, False)
OUT_OF_ORDER = False
EXECUTION_FINISHED = False
instr_count = -1
mem_count = -1
instr_queue = []
mem_dict = {}
R = RegisterFile()
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
    "BNEZ": 1,
    "HALT": 0,
    '*':-1
}
clock_cycle = 1
rs_int = [False, False, False, False]
rs_fp_mult = [False, False, False, False]
rs_fp_add = [False, False, False, False]



def main(argv):
    # Global System Flags
    global EXECUTION_FINISHED, instr_count, mem_count, instr_queue, mem_dict, clock_cycle
    # regular expression describing memory format
    # https://regex101.com/r/zY4hB0/3
    mem_finder = re.compile(ur"<(\d+)> ?<([-+]?\d*\.?\d*)>")
    # regular expression describing instruction format
    instr_finder = re.compile(ur"([A-Z]+)\s*(R?#?\d+)?,?\s*(R?#?\d+)?,?\s*(R?#?\d+.?\d*)?")
    print "Welcome to the program"
    if len(argv) != 1:  # highly robust input sanitation
        print "Wrong number of files!"
        return
    with open(argv[0]) as codefile:
        for line in codefile:
            line = line.partition('--')[0]
            if len(line) == 0:  # if trimmed line is empty, go to next iteration
                continue
            elif line[0].isdigit():  # must be a count
                if instr_count == -1:
                    instr_count = line
                elif mem_count == -1:
                    mem_count = line
            elif line[0].isalpha():  # must be an instruction
                if line == "HALT\n":
                    instr_queue.append(Instruction("HALT", ["", "", ""]))
                    continue
                opcode = re.findall(instr_finder, line)[0][0]
                operands =  re.findall(instr_finder, line)[0][1:]
                instr_queue.append(Instruction(opcode, operands))
            elif line[0] is '<':  # must be a memory thing
                address, value = re.findall(mem_finder, line)[0]
                mem_dict[address] = value
    instr_queue.append(Instruction('*', "")) #append dummy instruction that signifies the end

    while(not EXECUTION_FINISHED):
        if instr_queue[program_counter].opcode !='*':
            issue(instr_queue[program_counter])
        execute()
        write_result()


        clock_cycle += 1



    print "Finished with " + clock_cycle + " clock cycles."


def issue(instruction):
    global rs_int, rs_fp_add, rs_fp_mult, program_counter
    succeeds = False
    rs_index = 0
    rs_type = None
    if instruction.opcode[0] is 'B' or instruction.opcode in ["ADD" , "SUB"]:
        for idx, station in enumerate(rs_int):
            if station is False:
                rs_int[idx] = True
                succeeds = True
                rs_index = idx
                rs_type = "INT"
            if succeeds:
                break
    elif instruction.opcode in ["FPADD", "FPSUB"]:
        for idx, station in enumerate(rs_fp_add):
            if station is False:
                rs_fp_add[idx] = True
                succeeds = True
                rs_index = idx
                rs_type = "FPADD"
            if succeeds:
                break
    elif instruction.opcode in  ["FPMULT", "FPDIV"]:
        for idx, station in enumerate(rs_fp_mult):
            if station is False:
                rs_fp_mult[idx] = True
                succeeds = True
                rs_index = idx
                rs_type = "FPMULT"
            if succeeds:
                break
    elif instruction.opcode in ["LOAD", "MOV", "STR", "HALT"]:
        succeeds = True



    dest = reorder_buffer.check_destinations(instruction.destination)
    src1 = reorder_buffer.check_source1(instruction.source1)
    src2 = reorder_buffer.check_source2(instruction.source2)


    if succeeds == True:
        if instruction.opcode != '*':
            program_counter += 1
        rob_entry = reorder_buffer.add_entry(instruction, clock_cycle, rs_index, rs_type)
        if src1 is not -1:
            reorder_buffer.entry_list[rob_entry].source1_ROB = src1
            reorder_buffer.entry_list[rob_entry].source1_valid = False
        if src2 is not -1:
            reorder_buffer.entry_list[rob_entry].source2_ROB = src2
            reorder_buffer.entry_list[rob_entry].source2_valid = False

def execute():
    global EXECUTION_FINISHED
    for entry in reorder_buffer.entry_list:
        if entry.ready is False and entry.cycle_issued != clock_cycle:
            if entry.executing is False:
                if entry.source1_valid is True and entry.source2_valid is True:
                    entry.executing = True
                    if entry.opcode is "FPMULT":
                        # change clock cycles for special cases
                        if entry.source1 in [-1, 1, 0] or entry.source2 in [-1,1,0]:
                            entry.remaining_cycles = 1
                        elif pwr_of_two(entry.source1) or pwr_of_two(entry.source2):
                            entry.remaining_cycles = 2
            elif entry.executing is True:
                entry.remaining_cycles -= 1
        if entry.remaining_cycles <= 0 and entry.write_back_success is False:
            operand1, operand2 = entry.get_values()
            if entry.opcode == 'FPADD' or entry.opcode == 'ADD':
                entry.result = operand1 + operand2
            elif entry.opcode == 'FPSUB' or entry.opcode == 'SUB':
                entry.result = operand1 - operand2
            elif entry.opcode == 'FPMULT':
                entry.result = operand1 * operand2
            elif entry.opcode == 'FPDIV':
                entry.result = operand1 / operand2
            elif entry.opcode == 'LOAD':
                entry.result = operand2
            elif entry.opcode == 'MOV':
                entry.result = operand2
            elif entry.opcode == 'STR':
                entry.result = operand1
            elif entry.opcode[0] == 'B':
                branch(entry)
            elif entry.opcode == 'HALT':
                done = True
                for entry in reorder_buffer.entry_list:
                    if entry.write_back_success is False and entry.opcode != 'HALT':
                        done = False
                        break
                if done:
                    EXECUTION_FINISHED = True

            entry.ready = True


def write_result():
    global program_counter
    WAW_FLAG = False
    for idx, entry in enumerate(reorder_buffer.entry_list):
        op1, op2 = entry.get_values()
        if entry.ready is True and entry.executing is True:
            # write back next clock cycle
            entry.executing = False
        elif entry.ready is True and entry.executing is False:
            # time to write back!
            for other_entry in reorder_buffer.entry_list[:idx]:
                if other_entry.destination == entry.destination and other_entry.write_back_success is False:
                    WAW_FLAG = True
            if not WAW_FLAG and not entry.speculative:
                if entry.opcode == 'STR':
                    mem_dict[op2] = entry.result
                # branch prediction logic
                else:
                    R[int(entry.destination[1:])] = entry.result
                if entry.rs_type == 'INT':
                    rs_int[entry.rs_index] = False
                elif entry.rs_type == 'FPADD':
                    rs_fp_add[entry.rs_index] = False
                elif entry.rs_type == 'FPMULT':
                    rs_fp_mult[entry.rs_index] = False
                entry.write_back_success = True
                for other_entry in reorder_buffer.entry_list: # resolve RAW hazards
                    if other_entry.source1_ROB == idx:
                        other_entry.source1_valid = True
                    if other_entry.source2_ROB == idx:
                        other_entry.source2_valid = True

                continue












def pwr_of_two(num):
    return num != 0 and ((num & (num - 1)) == 0)

def branch(entry):
    print "Branch"



# magic code than runs main
if __name__ == "__main__":
    for file in sys.argv[1:]:
        main([file])
        print "\n\n\n"


