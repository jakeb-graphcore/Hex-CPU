import cocotb
from transactors import InstructionMemoryTransactor, DataMemoryTransactor, DynamicInstructionMemoryTransactor
from monitors import ArchStateMonitor
from transactions import MemTransaction
from drivers import ResetDriver
from models import CPUModel
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import tb_config

class TB:
    def __init__(self, entity, seed):
        self.data_read_scoreboard_enabled = tb_config.data_read_scoreboard_enabled
        self.entity = entity
        self.clock = Clock(entity.i_clk, 1, units="ns")
        self.instruction_mem_transactor = DynamicInstructionMemoryTransactor(entity, entity.i_clk, self.instruction_mem_callback) if tb_config.use_dynamic_instruction_transactor else InstructionMemoryTransactor(entity, entity.i_clk, self.instruction_mem_callback, enable_scoreboard=tb_config.instruction_enable_scoreboard, end_of_test_scoreboard_check=tb_config.instruction_end_of_test_scoreboard_check)
        self.data_mem_transactor = DataMemoryTransactor(entity, entity.i_clk, self.data_mem_callback, enable_scoreboard=tb_config.data_enable_scoreboard, read_scoreboard_enabled=self.data_read_scoreboard_enabled, end_of_test_scoreboard_check=tb_config.data_end_of_test_scoreboard_check)
        self.arch_state_monitor = ArchStateMonitor(entity.u_arch_monitor, entity.i_clk, seed) if tb_config.use_arch_state_monitor else None
        self.reset_driver = ResetDriver(entity, entity.i_clk)
        self.cpu_model = CPUModel()

    async def reset(self):
        self.cpu_model.reset()
        await self.reset_driver.reset()

    def instruction_mem_callback(self, transaction : MemTransaction):
        pass

    def data_mem_callback(self, transaction : MemTransaction):
        pass

    def end_of_test(self):
        self.instruction_mem_transactor.end_of_test()
        self.data_mem_transactor.end_of_test()

    async def run(self, code=("32","43","D0","20","10","ff","9e"), data_memory=tuple()):
        self.cpu_model.load_instructions(code)
        if self.arch_state_monitor is not None:
            self.arch_state_monitor.load_instructions(code)
        self.cpu_model.execute_program()
        data_mem_queue = self.cpu_model.data_queue if self.data_read_scoreboard_enabled else self.cpu_model.data_write_queue
        self.data_mem_transactor.expected(data_mem_queue)
        self.instruction_mem_transactor.load_memory(code)
        self.data_mem_transactor.load_memory(data_memory)
        cocotb.start_soon(self.clock.start())
        await self.reset()
        await cocotb.triggers.First(ClockCycles(self.entity.i_clk, 10000), cocotb.triggers.Combine(self.instruction_mem_transactor.transactor_finished.wait(), self.data_mem_transactor.transactor_finished.wait()))
        self.end_of_test()
