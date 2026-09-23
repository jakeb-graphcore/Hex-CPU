import drivers
import monitors
import mem_model
import models

from transactions import MemTransaction
from cocotb_bus.scoreboard import Scoreboard
from random import Random

class MemoryTransactor:
    def __init__(self, entity, clock, testbench_callback, driver, monitor, enable_scoreboard=True, end_of_test_scoreboard_check=True):
        self.driver = driver
        self.monitor = monitor
        self.mem_model = mem_model.MemoryModel()
        self.testbench_callback = testbench_callback
        self.scoreboard = Scoreboard(entity)
        self.expected_transactions = []
        if enable_scoreboard:
            self.scoreboard.add_interface(self.monitor, self.expected_transactions)
        self.transactor_finished = self.monitor.bus_quiesce
        self.end_of_test_scoreboard_check = end_of_test_scoreboard_check

    def load_memory(self, code):
        if isinstance(code, str):
            code = code.split("\n")
        int_code = []
        for instr in code:
            if isinstance(instr, str):
                int_instr = int(instr, 16)
            else:
                int_instr = int(instr)
            int_code.append(int_instr)
        while len(int_code) < 256:
            int_code.append(0)
        self.mem_model.block_write(0, int_code)

    def monitor_callback(self, transaction : MemTransaction):
        self.testbench_callback(transaction)
        if transaction.is_read:
            mem_val = self.mem_model.read(transaction.addr)
            self.driver.append(MemTransaction(True, transaction.addr, mem_val))
        else:
            self.mem_model.write(transaction.addr, transaction.data)
            
    def assert_expected_transactions_empty(self):
        assert len(self.expected_transactions) == 0, f"Transactions left in {self!r}. {self.expected_transactions!r}"

    def end_of_test(self):
        if self.end_of_test_scoreboard_check:
            self.assert_expected_transactions_empty()

    def diable_monitor(self):
        self.monitor.disable()

    def expected(self, trans):
        try:
            iterator = iter(trans)
        except TypeError:
            iterator = iter((trans,))
        for t in iterator:
            self.expected_transactions.append(t)

class InstructionMemoryTransactor(MemoryTransactor):
    def __init__(self, entity, clock, testbench_callback, enable_scoreboard=True, end_of_test_scoreboard_check=True):
        driver = drivers.InstructionMemoryDriver(entity, clock)
        monitor = monitors.InstructionMemoryMonitor(entity, clock, self.monitor_callback, read_scoreboard_enabled=False)
        super().__init__(entity, clock, testbench_callback, driver, monitor, enable_scoreboard, end_of_test_scoreboard_check=end_of_test_scoreboard_check)

class DataMemoryTransactor(MemoryTransactor):
    def __init__(self, entity, clock, testbench_callback, enable_scoreboard=True, read_scoreboard_enabled=False, end_of_test_scoreboard_check=True):
        driver = drivers.DataMemoryDriver(entity, clock)
        monitor = monitors.DataMemoryMonitor(entity, clock, self.monitor_callback, read_scoreboard_enabled=read_scoreboard_enabled)
        super().__init__(entity, clock, testbench_callback, driver, monitor, enable_scoreboard, end_of_test_scoreboard_check=end_of_test_scoreboard_check)

class DynamicInstructionMemoryTransactor(InstructionMemoryTransactor):
    def __init__(self, entity, clock, testbench_callback):
        self.cpu_model = models.CPUModel()
        seed = 1234
        self.num_of_instructions_to_serve = 10000;
        self.rand = Random(seed)
        self.num_of_instructions_served = 0;
        
        
        super().__init__(entity, clock, testbench_callback, enable_scoreboard=False, end_of_test_scoreboard_check=False)

    def next_instruction(self, transaction: MemTransaction):
        # TODO: (TASK 5) Implement your Dynamic Instruction Transactor here.
        # Start with the simplest way, return a random instruction. Could have a dynamic instruction memory for this. 

        instruction = self.rand.randint(0, 255);
        print(f"Insruction: {instruction}")
        self.num_of_instructions_served += 1;

        # send second end of statement
        if self.num_of_instructions_to_serve - self.num_of_instructions_served == 0:
            return 0xff

        # send last end of statement 
        if self.num_of_instructions_to_serve - self.num_of_instructions_served == -1:
            return 0x9e

        return instruction

    # changes such that we check against the generated instruction, by using fetch override.
    def monitor_callback(self, transaction: MemTransaction):
        mem_val = self.next_instruction(transaction)

        response = MemTransaction(True, transaction.addr, mem_val)
        self.testbench_callback(response)

        self.cpu_model.execute_instruction(fetch_override=mem_val)
        self.driver.append(response)
