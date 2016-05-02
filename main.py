#!/usr/bin/python

import re
import sys
from pprint import pprint


# sys.argv is command line args


# data structure to represent an instruction. Holds the opcode and the operands as properties, as well as
# cycles needed to finsh running
class Instruction():
    def __init__(self, opcode, argv):
        operands = []
        self.opcode = opcode
        for operand in argv:
            operands.append(operand.strip(','))
        # Sort operands based on opcode
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
        elif opcode in ['BGT', 'BLT', 'BGE', 'BLE', 'BZ', 'BNEZ']:
            self.destination = None
            self.source1 = operands[0]
            self.source2 = operands[1]
        elif opcode == 'STR':
            self.destination = None
            self.source1 = operands[0]
            self.source2 = operands[1]
        else:
            self.destination = None
            self.source1 = None
            self.source2 = None

        # sets total cycles to completion (based on global dictionary of cycle counts)
        self.total_cycles = cycle_dict[self.opcode]



# data structure to represent register bank. extends dictionary allowing [] operator access
class RegisterFile(dict):
    def __init__(self, *args, **kwargs):
        super(RegisterFile, self).__init__(*args, **kwargs)
        self.itemlist = super(RegisterFile, self).keys()
        for x in xrange(16):
            self[x] = 0
        self[0] = 2
        self[1] = 1
        self[4] = -1


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




# Wraps instructions once they get into reorder buffer, keeping original  instruction from being changed. Holds a ton
# of properties about the instruction's execution status.
class ReorderBufferEntry():
    def __init__(self, instruction, clock_cycle, rs_index, rs_type):
        self.opcode = instruction.opcode
        self.destination = instruction.destination
        self.source1 = instruction.source1
        self.source1_ROB = None # holds the reorder buffer index of the dependant instruction
        self.source1_valid = True # is the source1 valid to read from?
        self.source2 = instruction.source2
        self.source2_ROB = None
        self.source2_valid = True
        self.total_cycles = instruction.total_cycles
        self.result = None
        self.speculative = False # is the instruction issued speculatively by a branch?
        self.remaining_cycles = self.total_cycles
        self.executing = False
        self.ready = False # instruction has executed and is ready to write back
        self.cycle_issued = clock_cycle
        self.rs_index = rs_index # index in the reservation station instruction holds
        self.rs_type = rs_type # which RS the instruction goes into
        self.write_back_success = False # has the result been written back to memeory?
        self.flushed = False # removed from ROB due to incorrect branch prediction
        if self.opcode[0]  == 'B':
            self.branch_prediction = None # was the last branch prediction correct?
            self.PC_before_predict = 0

    def get_values(self):
        # returns the values at the memory locations specified by the operands. Return results should all be floating
        # point numbers
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




# data structure to hold all the ReorderBufferEntries. Probably could have just been a list, but class allows for
# additional functionality
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

    def check_source(self, value):
        # check data dependencies for the given value
        index = -1
        for idx, entry in enumerate(self.entry_list):
            if entry.destination is not None and entry.write_back_success is False and entry.flushed is False:
                if entry.destination == value:
                    index = idx
        return index #returns ROB index of dependency, or -1 if no dependency




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

# branching stuff
speculating = False
branch_stall = False
branches_taken = 0
last_branch_correct = True



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
# reservation stations
rs_int = [False, False, False, False]
rs_fp_mult = [False, False, False, False]
rs_fp_add = [False, False, False, False]
# data collection for analysis
stat_branch_predictions = 0
stat_branch_predictions_correct = 0



def main(argv):
    # Global System Flags
    global EXECUTION_FINISHED, instr_count, mem_count, instr_queue, mem_dict, clock_cycle, stat_branch_predictions_correct, stat_branch_predictions
    # regular expression describing memory format
    # https://regex101.com/r/zY4hB0/3
    mem_finder = re.compile(ur"<(\d+)> ?<([-+]?\d*\.?\d*)>")
    # regular expression describing instruction format
    instr_finder = re.compile(ur"([A-Z]+)\s*(R?#?[+-]?\d+)?,?\s*(R?#?[+-]?\d+)?,?\s*(R?#?[+-]?\d+.?\d*)?")
    print "Welcome to the program"
    if len(argv) != 1:  # highly robust input sanitation
        print "Wrong number of files!"
        return
    with open(argv[0]) as codefile:
        print "Running " + str(codefile)
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

    while(not EXECUTION_FINISHED):
        print "Clock cycle: " + str(clock_cycle)
        print "-----------"
        issue()
        execute()
        write_result()

        #for entry in reorder_buffer.entry_list:
        #   pprint(vars(entry))
        print "R6: " + str(R[6])
        print '\n'

        clock_cycle += 1

    print "branches taken : " + str(branches_taken)
    print "correctness ratio: " + str(stat_branch_predictions_correct) + "/" + str(stat_branch_predictions)
    print R[3]
    print "Finished with " + str(clock_cycle) + " clock cycles."


def issue():
    global rs_int, rs_fp_add, rs_fp_mult, program_counter, speculating, branch_stall
    succeeds = False
    rs_index = 0
    rs_type = None
    instruction = instr_queue[program_counter]
    if branch_stall is False:
        if instruction.opcode[0] == 'B' and speculating is False:
            for idx, station in enumerate(rs_int):
                if station is False:
                    rs_int[idx] = True
                    succeeds = True
                    rs_index = idx
                    rs_type = "INT"
                if succeeds:
                    branch_stall = True
                    break
        if instruction.opcode in ["ADD" , "SUB"]:
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
        elif instruction.opcode in ["LOAD", "MOV", "STR"]:
            succeeds = True
        elif instruction.opcode == 'HALT':
            succeeds = True
            for other_entry in reorder_buffer.entry_list:
                if other_entry.opcode == 'HALT' and other_entry.flushed is False:
                    succeeds = False

    # check for data dependencies
    #dest = reorder_buffer.check_destinations(instruction.destination)
    src1 = reorder_buffer.check_source(instruction.source1)
    src2 = reorder_buffer.check_source(instruction.source2)


    if succeeds == True:
        if instruction.opcode != 'HALT':
            program_counter += 1
        rob_entry = reorder_buffer.add_entry(instruction, clock_cycle, rs_index, rs_type)
        if speculating is True:
            reorder_buffer.entry_list[rob_entry].speculative = True
        # if there's a data dependency, set it up in the ROB entry
        if src1 is not -1:
            reorder_buffer.entry_list[rob_entry].source1_ROB = src1
            reorder_buffer.entry_list[rob_entry].source1_valid = False
        if src2 is not -1:
            reorder_buffer.entry_list[rob_entry].source2_ROB = src2
            reorder_buffer.entry_list[rob_entry].source2_valid = False

def execute():
    global EXECUTION_FINISHED, ZERO, NEGATIVE, OVERFLOW, speculating, branch_stall, stat_branch_predictions
    for entry in reorder_buffer.entry_list:
        if entry.ready is False and entry.cycle_issued != clock_cycle:
            if entry.executing is False:
                if entry.source1_valid is True and entry.source2_valid is True:
                    entry.executing = True
                    if entry.opcode == 'FPMULT':
                        # change clock cycles for special cases
                        op1, op2 = entry.get_values()
                        if op1 in [-1, 1, 0] or op2 in [-1,1,0]:
                            entry.remaining_cycles = 1
                        elif pwr_of_two(op1) or pwr_of_two(op2):
                            entry.remaining_cycles = 2
                elif entry.source2_valid is True and speculating is False:
                    if entry.opcode[0] == 'B':
                        branch_predict_2b(entry)
                        stat_branch_predictions += 1
                        speculating = True
                        branch_stall = False
            elif entry.executing is True:
                entry.remaining_cycles -= 1
        if entry.remaining_cycles <= 0 and entry.write_back_success is False and entry.flushed is False and entry.ready is False:
            # Actually run the code
            operand1, operand2 = entry.get_values()
            if entry.opcode == 'FPADD' or entry.opcode == 'ADD':
                entry.result = operand1 + operand2
                if entry.result > 2 ** 32:
                    OVERFLOW = True
                    entry.result = (entry.result) % (2 ** 32)
                entry.ready = True
            elif entry.opcode == 'FPSUB' or entry.opcode == 'SUB':
                entry.result = operand1 - operand2
                entry.ready = True
            elif entry.opcode == 'FPMULT':
                entry.result = operand1 * operand2
                if entry.result > 2 ** 32:
                    OVERFLOW = True
                    entry.result = (entry.result) % (2 ** 32)
                entry.ready = True
            elif entry.opcode == 'FPDIV':
                entry.result = operand1 / operand2
                entry.ready = True
            elif entry.opcode == 'LOAD':
                entry.result = operand2
                entry.ready = True
            elif entry.opcode == 'MOV':
                entry.result = operand2
                entry.ready = True
            elif entry.opcode == 'STR':
                entry.result = operand1
                entry.ready = True
            elif entry.opcode[0] == 'B':
                branch(entry)
                entry.ready = True
                branch_stall = False
            elif entry.opcode == 'HALT':
                done = True
                for entry_other in reorder_buffer.entry_list:
                    if entry_other.write_back_success is False and entry_other.flushed is False and entry_other.opcode != 'HALT':
                        done = False
                        break
                if done:
                    EXECUTION_FINISHED = True

            if entry.result == 0:
                ZERO = True
            if entry.result < 0:
                NEGATIVE = True




def write_result():
    global program_counter
    for idx, entry in enumerate(reorder_buffer.entry_list):
        WAW_FLAG = False
        op1, op2 = entry.get_values()
        if entry.ready is True and entry.executing is True:
            # write back next clock cycle
            entry.executing = False
        elif entry.ready is True and entry.executing is False:
            # time to write back!
            for other_entry in reorder_buffer.entry_list[:idx]:
                if other_entry.destination is not None and other_entry.destination == entry.destination and other_entry.write_back_success is False:
                    WAW_FLAG = True
            if not WAW_FLAG and not entry.speculative and not entry.write_back_success and not entry.flushed:
                if entry.opcode == 'STR':
                    mem_dict[op2] = entry.result
                elif entry.opcode == 'LOAD':
                    R[int(entry.destination[1:])] = entry.result
                elif entry.opcode == 'HALT':
                    continue
                elif not entry.opcode[0] == 'B':
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
    if num % 1 != 0.0:
        return False
    num = int(num)
    return num != 0 and ((num & (num - 1)) == 0)

def branch(entry):
    # Non speculatively execute the branch
    global program_counter, speculating, branches_taken, stat_branch_predictions_correct, last_branch_correct
    branch_yn = False
    op1, op2 = entry.get_values()

    if entry.opcode == 'BR':
        branch_yn = True
    elif entry.opcode == 'BZ':
        if op1 == 0:
            branch_yn = True
    elif entry.opcode == 'BGT':
        if op1 > 0:
            branch_yn = True
    elif entry.opcode == 'BLT':
        if op1 < 0:
            branch_yn = True
    elif entry.opcode == 'BGE':
        if op1 >= 0:
            branch_yn = True
    elif entry.opcode == 'BLE':
        if op1 <= 0:
            branch_yn = True
    elif entry.opcode == 'BNEZ':
        if op1 != 0:
            branch_yn = True

    entry.result = branch_yn

    if branch_yn:
        branches_taken += 1
        if entry.branch_prediction is True:
            stat_branch_predictions_correct += 1
            last_branch_correct = True
            for other_entry in reorder_buffer.entry_list:
                if other_entry.speculative is True:
                    other_entry.speculative = False
        elif entry.branch_prediction is False:
            last_branch_correct = False
            for other_entry in reorder_buffer.entry_list:
                if other_entry.speculative is True:
                    #other_entry.speculative = False
                    if other_entry is not entry:
                        other_entry.flushed = True
            program_counter = entry.PC_before_predict + int(op2)
        elif entry.branch_prediction is None:
            program_counter += int(op2)
    else:
        if entry.branch_prediction is True:
            last_branch_correct = False
            for other_entry in reorder_buffer.entry_list:
                if other_entry.speculative is True:
                    #other_entry.speculative = False
                    if other_entry is not entry:
                        other_entry.flushed = True
            program_counter = entry.PC_before_predict # + int(op2)
        elif entry.branch_prediction is False:
            stat_branch_predictions_correct += 1
            last_branch_correct = True
            for other_entry in reorder_buffer.entry_list:
                if other_entry.speculative is True:
                    other_entry.speculative = False

    speculating = False



# Branch predict: Always Taken
def branch_predict_at(entry):
    # predicts always taken
    global program_counter
    op1, op2 = entry.get_values()
    entry.PC_before_predict = program_counter
    entry.branch_prediction = True
    program_counter += int(op2)


# Branch predict: Always Not Taken
def branch_predict_ant(entry):
    # predicts always not taken
    global program_counter
    op1, op2 = entry.get_values()
    entry.PC_before_predict = program_counter
    entry.branch_prediction = False
    #program_counter += int(op2)


# Branch Predict: One bit branch predictor
state_1b = False # not taken
def branch_predict_1b(entry):
    global state_1b, program_counter, last_branch_correct
    # dynamic branch prediction
    if (last_branch_correct is False):
        state_1b = ~state_1b
    # execute branch prediction
    if(state_1b):
        branch_predict_at(entry)
    else:
        branch_predict_ant(entry)





# Branch Predict: Two bit branch predictor
state_2b = 0 #strongly not taken
# 0 - strongly not taken
# 1 - weakly not taken
# 2 - weakly taken
# 3 - strong taken
def branch_predict_2b(entry):
    global state_2b, program_counter, last_branch_correct
    # dynamic predictor
    if (last_branch_correct is False):
        if (state_2b <= 1): # not taken
            state_2b += 1
        else: # taken
            state_2b -= 1
    else: #prediction correct
        if (state_2b == 1):
            state_2b -= 1
        elif (state_2b == 2):
            state_2b += 1
    # execute prediction
    if (state_2b <= 1):
        branch_predict_ant(entry)
    else:
        branch_predict_at(entry)






def check_done():
    global EXECUTION_FINISHED
    done = True
    for entry_other in reorder_buffer.entry_list:
        if entry_other.write_back_success is False and entry_other.opcode != 'HALT':
            done = False
            break
    if done:
        EXECUTION_FINISHED = True


# magic code that runs main
if __name__ == "__main__":
    for file in sys.argv[1:]:
        main([file])
        print "\n\n\n"


