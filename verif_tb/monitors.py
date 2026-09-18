import cocotb

from cocotb_bus.monitors import BusMonitor
from cocotb.triggers import RisingEdge, ReadOnly

from transactions import MemTransaction
from models import CPUModel
from coverage import Covergroup
from instr_encodings import InstrEncoding

class MemoryMonitor(BusMonitor):
    def __init__(self, entity, clock, callback, read_scoreboard_enabled=True, mon_name=""):
        super().__init__(entity, None, clock, callback=callback)
        self.bus_quiesce = cocotb.triggers.Event()
        self.enabled = True
        self.callback = callback
        self.read_scoreboard_enabled = read_scoreboard_enabled
        self.mon_name = mon_name

    def sig_val(self, ident):
        if not getattr(self.bus, ident).value.is_resolvable:
            raise ValueError(f"{self.mon_name} observed that signal {ident} has value {getattr(self.bus, ident).value}. This is not resolvable to an integer.")
        return int(getattr(self.bus, ident).value)

    def disable(self):
        self.enabled = False

    @cocotb.coroutine
    async def _monitor_recv(self):
        count_quiesce = 0
        while True:
            await RisingEdge(self.clock)
            await ReadOnly()
            if self.rd_en():
                if self.enabled and self.read_scoreboard_enabled:
                    self._recv(self.rd_trans())
                elif self.enabled:
                    self.callback(self.rd_trans())
            elif self.wr_en():
                print("Monitor writing", self, self.enabled, self.wr_trans())
                if self.enabled:
                    self._recv(self.wr_trans())
                count_quiesce = 0
            else:
                count_quiesce += 1
                # If we don't write anything to memory for 1000 cycles, memory bus is quiesced.
                if count_quiesce == 1000:
                    self.bus_quiesce.set()

    def rd_en(self):
        raise NotImplementedError

    def wr_en(self):
        raise NotImplementedError

    def rd_trans(self):
        raise NotImplementedError

    def wr_trans(self):
        raise NotImplementedError

class InstructionMemoryMonitor(MemoryMonitor):
    def __init__(self, entity, clock, callback, read_scoreboard_enabled=True, mon_name="Instruction Memory Monitor"):
        self._signals = ["o_instr_addr", "o_instr_rd_en"]
        super().__init__(entity, clock, callback, read_scoreboard_enabled, mon_name=mon_name)

    def rd_en(self):
        return bool(self.sig_val("o_instr_rd_en"))

    def wr_en(self):
        return False

    def rd_trans(self):
        return MemTransaction(True, self.sig_val("o_instr_addr"), None)

    def wr_trans(self):
        return

class DataMemoryMonitor(MemoryMonitor):
    def __init__(self, entity, clock, callback, read_scoreboard_enabled=True, mon_name="Data Memory Monitor"):
        self._signals = ["o_data_addr", "o_data_wr_data", "o_data_wr_en", "o_data_rd_en"]
        super().__init__(entity, clock, callback, read_scoreboard_enabled, mon_name=mon_name)

    def rd_en(self):
        return bool(self.sig_val("o_data_rd_en"))

    def wr_en(self):
        return bool(self.sig_val("o_data_wr_en"))

    def rd_trans(self):
        return MemTransaction(True, self.sig_val("o_data_addr"), None)

    def wr_trans(self):
        return MemTransaction(False, self.sig_val("o_data_addr"), self.sig_val("o_data_wr_data"))

class ArchStateMonitor(BusMonitor):
    def __init__(self, entity, clock, seed, mon_name="Arch State Monitor", checker_enabled=True, coverage_enabled=True):
        self.seed = seed
        self.mon_name = mon_name
        self.model = CPUModel()
        self._signals = ["retire", "pc", "oreg", "areg", "breg"]
        self.checker_enabled = checker_enabled
        self.coverage_enabled = coverage_enabled
        self.covergroup = Covergroup()
        self.define_coverage()
        self.covergroup.gen_buckets()
        self.model_finished = False
        super().__init__(entity, None, clock)

    def sig_val(self, ident):
        if not getattr(self.bus, ident).value.is_resolvable:
            raise ValueError(f"{self.mon_name} observed that signal {ident} has value {getattr(self.bus, ident).value}. This is not resolvable to an integer.")
        return int(getattr(self.bus, ident).value)

    def step_model(self):
        # May need to edit for TASK 5.
        self.model_finished = self.model.execute_instruction(fetch_override=None)

    def load_instructions(self, code):
        self.model.load_instructions(code)

    def define_coverage(self):
        self.covergroup.add_coverpoint("all_instructions")
        self.covergroup["all_instructions"].add_axis("instr", [i.name for i in InstrEncoding])
        # TODO: (TASK 3) Define your coverage here.

    def collect_coverage(self):
        # TODO: (TASK 3) Collect your coverage here.
        instr_executed = self.model.prev_instr
        instr_name = InstrEncoding((instr_executed >> 4) & 0xf).name
        self.covergroup["all_instructions"].incr((instr_name,))
        if self.model_finished:
            self.covergroup.sub_report(self.seed)
            self.covergroup.report()

    @cocotb.coroutine
    async def _monitor_recv(self):
        while True:
            await RisingEdge(self.clock)
            await ReadOnly()
            if self.checker_enabled and not self.model_finished and bool(self.sig_val("retire")):
                self.step_model()
                assert self.sig_val("pc") == self.model.pc, f"PC mismatch. Expected: 0x{self.model.pc:x} Received: 0x{self.sig_val('pc'):x}"
                assert self.sig_val("oreg") == self.model.oreg, f"OREG mismatch. Expected: 0x{self.model.oreg:x} Received: 0x{self.sig_val('oreg'):x}"
                assert self.sig_val("areg") == self.model.areg, f"AREG mismatch. Expected: 0x{self.model.areg:x} Received: 0x{self.sig_val('areg'):x}"
                assert self.sig_val("breg") == self.model.breg, f"BREG mismatch. Expected: 0x{self.model.breg:x} Received: 0x{self.sig_val('breg'):x}"
                self.collect_coverage()
