from tb import TB
import testgen
from random import Random
import cocotb
import os
import tb_config


root_rand = Random()
root_rand.seed(tb_config.ROOT_SEED)
async def run_test(dut, test_case=None):
    test_generator, seed, operand = test_case

    # If an operand is supplied, randomly generate one.
    if operand == None:
        rand = Random(seed)
        operand = rand.randint(0, 15)

    tb = TB(dut, seed)
    code = test_generator(operand)
    await tb.run(code)

def log_seeds(root_seed, test_seeds):
    if not os.path.isdir(tb_config.LOG_ROOT):
        os.mkdir(tb_config.LOG_ROOT)
    path = os.path.join(tb_config.LOG_ROOT, "seeds.log")
    with open(path, "w") as file:
        file.write(f"root_seed : {root_seed}\n")
        file.write("test_num : seed\n")
        for i, seed in enumerate(test_seeds):
            file.write(f"{i+1:03} : 0x{seed:08x}\n")

def clear_coverage():
    for filename in os.listdir(tb_config.LOG_ROOT):
        if filename.startswith("coverage") or filename.startswith("sub_coverage"):
            os.remove(os.path.join(tb_config.LOG_ROOT, filename))

if tb_config.TEST_SEEDS_OVERRIDE is None:
    test_seeds = [root_rand.randint(0, 0xffff_ffff) for _ in range(tb_config.NUM_TESTS)]
    log_seeds(tb_config.ROOT_SEED, test_seeds)
else:
    test_seeds = tb_config.TEST_SEEDS_OVERRIDE
    log_seeds("None (seeds overwrite)", test_seeds)

clear_coverage()

tf = cocotb.regression.TestFactory(run_test)

# Tests to run
test_generators = [
    testgen.directed_1,
    testgen.directed_2,
    testgen.directed_3,
    testgen.test_randomly,
    testgen.test_randomly,
    testgen.test_randomly,
    testgen.test_randomly,
    testgen.test_everything,
]

# Branch test generators
test_branches = [
    testgen.br_with_operand,
    testgen.brb_with_operand,
    testgen.brz_taken_with_operand,
    testgen.brn_taken_with_operand,
]

# Give each test a unique(ish) number associated with it
test_cases = [
    (
        generator,
        root_rand.randint(0, 0xffff_ffff),
        None
    )
    for generator in test_generators
]

# test every branch exhaustively
test_branches = [
    (   test_branch, 
        root_rand.randint(0, 0xffff_ffff), 
        i
    ) 
    for test_branch in test_branches for i in range(0, 16)]

test_cases.extend(test_branches)

tf.add_option(name="test_case", optionlist=test_cases)
tf.generate_tests()