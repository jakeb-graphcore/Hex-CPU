from tb import TB
import testgen
from random import Random
import cocotb
import os
import tb_config


root_rand = Random()
root_rand.seed(tb_config.ROOT_SEED)
async def run_test(dut, seed=0):
    rand = Random()
    rand.seed(seed)
    tb = TB(dut, seed)
    await tb.run(testgen.main_testgen_control(rand))

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
tf.add_option(name="seed", optionlist=test_seeds)
tf.generate_tests()