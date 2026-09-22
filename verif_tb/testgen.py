from instr_encodings import InstrEncoding
from itertools import accumulate
from random import Random
# Note : use the rand object in main_testgen_control to generate random values. Don't use the random package directly to avoid random stability issues.

def directed_1(operand):
    return ["32","43","D0","20","10","ff","9e"]

def directed_2(operand):
    return ["91", "00", "00", "ff", "9e"]

def directed_3(operand):
    return ["32", "ff", "9e"]

# TODO: How to make it so both these tests are run

# Test every possible instruction in order
def test_everything(_operand):
    # For now, remove branch operations and test them seperatly (as the instructions are layed out such taht they loop the model).
    all_instructions = [str(hex(i)) for i in range(0, 256) if not (144 <= i <= 207 )]
    all_instructions.append("0x9e") # Wanted end string
    return all_instructions


# Test branching operations
def test_brainching():
    pass


# GPT's branch forward operand amount
def br_with_operand(operand):
    assert 0 <= operand <= 15

    return [
        f"9{operand:x}",      # BR operand
        *(["31"] * operand),  # Instructions skipped
        "32",                 # Branch target
        "ff",
        "9e",
    ]

# GPT's branch forward with branch amount
def brz_taken_with_operand(operand):
    assert 0 <= operand <= 15

    return [
        f"a{operand:x}",
        *(["31"] * operand),
        "32",
        "ff",
        "9e",
    ]

# GPT's branch forward with operand
def brn_taken_with_operand(operand):
    assert 0 <= operand <= 15

    return [
        "f8",                 # Build 0x80
        "30",                 # areg = 0x80
        f"b{operand:x}",      # BRN operand
        *(["31"] * operand),
        "32",
        "ff",
        "9e",
    ]


# GPT's branch forward with operand
def brb_with_operand(operand):
    assert 0 <= operand <= 15

    return [
        "44",                 # breg = 4
        f"c{operand:x}",      # BRB with operand nibble
        "31",                 # Skipped
        "31",                 # Skipped
        "32",                 # Address 4
        "ff",
        "9e",
    ]

# Test randomly n times, doesnt use branch
def test_randomly(n: int):
    rand = Random()
    rand.seed(n)

    instructions = []
    for i in range(0, 240):
        instr = rand.randint(0, 254)
        if not (144 <= instr <= 207):
            instructions.append(instr)

    instructions.append("0xff")
    instructions.append("0x9e")

    return instructions
# Tests are randomly chosen. Use this to change the weighting of your tests.
TEST_WEIGHTS = {directed_1: 1, directed_2: 1}

def main_testgen_control():
#    total_weight = sum(TEST_WEIGHTS.values())
#    rand_val = rand.randint(1, total_weight)
#    for test, cumulative_weight in zip(TEST_WEIGHTS, accumulate(TEST_WEIGHTS.values())):
#        if rand_val <= cumulative_weight:
#            picked_test = test
#            break
#    return picked_test(rand)

    
    return test_everything();
