import cocotb

from cocotb_bus.monitors import BusMonitor
from cocotb.triggers import RisingEdge, ReadOnly

from collections import deque

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

        # Instructinos generated for dynamic instruction memory
        self.instruction_queue = deque();
        self.prefix_depth = 0
        self.memory_write_history = {}
        self.overwritten_addresses = set()
        self.pre_state = {}

        super().__init__(entity, None, clock)

    def sig_val(self, ident):
        if not getattr(self.bus, ident).value.is_resolvable:
            raise ValueError(f"{self.mon_name} observed that signal {ident} has value {getattr(self.bus, ident).value}. This is not resolvable to an integer.")
        return int(getattr(self.bus, ident).value)

    def step_model(self):
        # May need to edit for TASK 5.
        # Change so that we don't read straight from instruciton memory when dynamically generating (we do this by overriding fetch)
        
        
        self.pre_state = {
            "areg": int(self.model.areg),
            "breg": int(self.model.breg),
            "oreg": int(self.model.oreg),
            "pc": int(self.model.pc),
        }

        instruction = self.instruction_queue.popleft()
        self.model_finished = self.model.execute_instruction(fetch_override=instruction)

        # self.model_finished = self.model.execute_instruction(fetch_override=None)


    def load_instructions(self, code):
        self.model.load_instructions(code)

    # TODO: (TASK 3) Define your coverage here.
    def define_coverage(self):
        self.covergroup.add_coverpoint("all_instructions")
        self.covergroup["all_instructions"].add_axis("instr", [i.name for i in InstrEncoding])

        # Count the amount of instructions executed
        self.covergroup.add_coverpoint("num_instr_executed")
        self.covergroup["num_instr_executed"].add_axis("num_instr", ["num_instr"])


        # Test each opcode and operand
        self.covergroup.add_coverpoint("all_instructions_and_opcodes")
        self.covergroup["all_instructions_and_opcodes"].add_axis("instr_opcode", [instr.name for instr in InstrEncoding])
        self.covergroup["all_instructions_and_opcodes"].add_axis("operand", range(16))

        # Conditional branches have both reachable outcomes. BR and BRB are
        # unconditional, so including them would create impossible not-taken bins.
        self.covergroup.add_coverpoint("conditional_branch_outcomes")
        self.covergroup["conditional_branch_outcomes"].add_axis("instr", ["BRZ", "BRN"])
        self.covergroup["conditional_branch_outcomes"].add_axis("outcome", ["taken", "not_taken"])


        # Added coverage.
        self.covergroup.add_coverpoint("arithmetic_wraparound")
        self.covergroup["arithmetic_wraparound"].add_axis("instr", ["ADD", "SUB"])
        self.covergroup["arithmetic_wraparound"].add_axis("result", ["wrapped", "not_wrapped"])

        self.covergroup.add_coverpoint("prefix_handling")
        self.covergroup["prefix_handling"].add_axis(
            "event", ["single_prefix", "chained_prefix", "prefix_consumed"]
        )

        self.covergroup.add_coverpoint("memory_access_history")
        self.covergroup["memory_access_history"].add_axis(
            "event",
            ["first_write", "overwrite", "read_after_write", "read_after_overwrite"],
        )

    def collect_coverage(self):
        # TODO: (TASK 3) Collect your coverage here.
        instr_executed = self.model.prev_instr
        instr_name = InstrEncoding((instr_executed >> 4) & 0xf).name
        operand = instr_executed & 0xf

        oreg = self.model.oreg # I believe this may be set to 0 before we collect coverage. 
        areg = self.model.areg
        breg = self.model.breg

        self.covergroup["all_instructions"].incr((instr_name,))


        # count how many instructions have been executed
        self.covergroup["num_instr_executed"].incr(("num_instr",))


        # Report each instruction and its opcode
        self.covergroup["all_instructions_and_opcodes"].incr((instr_name, operand))

        self._collect_branch_coverage(instr_name)
        self._collect_arithmetic_coverage(instr_name)
        self._collect_prefix_coverage(instr_name)
        #self._collect_memory_coverage(instr_name)

        # report all coverage
        if self.model_finished:
            print("Writing Coverage Reports")
            self.covergroup.sub_report(self.seed)
            self.covergroup.report()


    
    def _collect_branch_coverage(self, instr_name):
        if instr_name == "BRZ":
            taken = self.pre_state["areg"] == 0
        elif instr_name == "BRN":
            taken = self.pre_state["areg"] > 127
        else:
            return

        outcome = ""
        if taken:
            outcome = "taken"
        else:
            outcome = "not_taken"

        self.covergroup["conditional_branch_outcomes"].incr((instr_name, outcome))


    # collects if a wraparound occurs
    def _collect_arithmetic_coverage(self, instr_name):
        if instr_name == "ADD":
            wrapped = self.pre_state["areg"] + self.pre_state["breg"] > 255
        elif instr_name == "SUB":
            wrapped = self.pre_state["areg"] - self.pre_state["breg"] < 0
        else:
            return

        result = ""
        if wrapped:
            result = "wrapped"
        else:
            result = "not_wrapped"

        self.covergroup["arithmetic_wraparound"].incr((instr_name, result))


    def _collect_prefix_coverage(self, instr_name):
            if instr_name == "PFIX":
                event = "single_prefix" if self.prefix_depth == 0 else "chained_prefix"
                self.prefix_depth += 1
                self.covergroup["prefix_handling"].incr((event,))
            elif self.prefix_depth > 0:
                self.covergroup["prefix_handling"].incr(("prefix_consumed",))
                self.prefix_depth = 0

    # return the last n instructions
    def get_last_n_instructions(self, n: int):
        return self.model.all_instructions[len(self.model.all_instructions) - n - 1 :len(self.model.all_instructions)]

    def push_instruction(self, instruction: int):
        self.instruction_queue.append(instruction)

    # forces the model to collect coverage and write it. Used when model timeouts.
    def force_collect_coverage(self): 
        print("Writing Coverage Reports")
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

                # check if we have too many clock cycles
                
                
                self.collect_coverage()
