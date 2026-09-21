# TB setup
instruction_enable_scoreboard = False
data_enable_scoreboard = True # Set to True to enable the scoreboard for the data memory transactor.
data_read_scoreboard_enabled = True # Set to False to disable the read request tracking in the data memory transactor.
instruction_end_of_test_scoreboard_check = False
data_end_of_test_scoreboard_check = True # Set to False to disable the end of test check that ensures the queue for the scoreboard of the data memory transactor is empty.
use_dynamic_instruction_transactor = False # Replaces regular memory based instruction transactor with dynamic instruction transactor. Set to True before beginning TASK 5.
use_arch_state_monitor = True # Monitors and checks the architectural state of the design. Set to True before beginning TASK 2.
# Test setup
ROOT_SEED = 0
NUM_TESTS = 1
TEST_SEEDS_OVERRIDE = None # Set to None to avoid override. Set to list of test seeds to override (e.g. If set to [0xdeadbeef, 0xffffffff], two tests will be run.)
# Logs
LOG_ROOT = "./sim_logs"
