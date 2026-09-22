from instr_encodings import InstrEncoding
from itertools import accumulate
from random import Random
# Note : use the rand object in main_testgen_control to generate random values. Don't use the random package directly to avoid random stability issues.

def directed_1(rand : Random):
    return ["32","43","D0","20","10","ff","9e"]

def directed_2(rand : Random):
    return ["91", "00", "00" "ff", "9e"]

def directed_3(rand : Random):
    return ["32", "ff", "9e"]

# TODO: How to make it so both these tests are run

# Test every possible instruction in order
def test_everything():
    # For now, remove branch operations and test them seperatly (as the instructions are layed out such taht they loop the model).
    all_instructions = [str(hex(i)) for i in range(0, 256) if not (144 <= i <= 207 )]
    all_instructions.append("0x9e") # Wanted end string

    return all_instructions





# Test randomly n times
def test_randomly(rand: Random, n: int):
    return [rand(0, 255) for i in range(0, n)]

# TODO: (TASK 4) Add your testgen tests here.

# Tests are randomly chosen. Use this to change the weighting of your tests.
TEST_WEIGHTS = {directed_1: 1, directed_2: 1}

def main_testgen_control(rand : Random):
#    total_weight = sum(TEST_WEIGHTS.values())
#    rand_val = rand.randint(1, total_weight)
#    for test, cumulative_weight in zip(TEST_WEIGHTS, accumulate(TEST_WEIGHTS.values())):
#        if rand_val <= cumulative_weight:
#            picked_test = test
#            break
#    return picked_test(rand)
    return directed_1(rand)
