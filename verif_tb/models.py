from transactions import MemTransaction
from mem_model import MemoryModel
from instr_encodings import InstrEncoding

class Reg(int):
    def __add__(self, other):
        return Reg((int(self) + int(other)) & 0xff)

    def __sub__(self, other):
        return Reg((int(self) - int(other)) % 0x100)

    def __lshift__(self, other):
        return Reg((int(self) << int(other)) & 0xff)

    def __rshift__(self, other):
        return Reg((int(self) >> int(other)) & 0xff)

    def __and__(self, other):
        return Reg(int(self) & int(other))

    def __or__(self, other):
        return Reg(int(self) | int(other))

class CPUModel:
    def __init__(self, instruction_memory=None, data_memory=None, instruction_fetch_cb=None, data_read_cb=None, data_write_cb=None):
        self.instruction_memory = MemoryModel() if instruction_memory is None else instruction_memory
        self.data_memory = MemoryModel() if data_memory is None else data_memory
        self.instruction_fetch_cb = self.default_instruction_fetch_cb if instruction_fetch_cb is None else instruction_fetch_cb
        self.data_read_cb = self.default_data_read_cb if data_read_cb is None else data_read_cb
        self.data_write_cb = self.default_data_write_cb if data_write_cb is None else data_write_cb
        self.instruction_trans_queue = []
        self.data_read_queue = []
        self.data_write_queue = []
        self.data_queue = []
        self.areg = Reg(0)
        self.breg = Reg(0)
        self.oreg = Reg(0)
        self.pc = Reg(0)
        self.prev_instr = None
        self.all_instructions = []

    def load_instructions(self, code):
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
        self.instruction_memory.block_write(0, int_code)

    def default_instruction_fetch_cb(self, trans):
        self.instruction_trans_queue.append(trans)

    def default_data_read_cb(self, trans):
        self.data_read_queue.append(trans)
        self.data_queue.append(trans)

    def default_data_write_cb(self, trans):
        self.data_write_queue.append(trans)
        self.data_queue.append(trans)

    def reset(self):
        self.areg = Reg(0)
        self.breg = Reg(0)
        self.oreg = Reg(0)
        self.pc = Reg(0)

    def log_fetched_instruction(self, mem_trans):
        print(f"Fetching {mem_trans} in instr memory ({InstrEncoding(mem_trans.data >> 4).name} 0x{mem_trans.data & 0xf:02x}).")

    def log_data_read(self, mem_trans):
        print(f"Reading  {mem_trans} in data memory.")

    def log_data_write(self, mem_trans):
        print(f"Writing  {mem_trans} in data memory.")

    def fetch_instruction(self, pc):
        fetched_instruction = self.instruction_memory.read(pc)
        mem_trans = MemTransaction(True, pc, fetched_instruction)
        self.log_fetched_instruction(mem_trans)
        self.instruction_fetch_cb(mem_trans)
        return Reg(fetched_instruction)

    def data_read(self, addr):
        addr = int(addr)
        data = self.data_memory.read(addr)
        mem_trans = MemTransaction(True, addr, None)
        self.log_data_read(MemTransaction(True, addr, data))
        self.default_data_read_cb(mem_trans)
        return Reg(data)

    def data_write(self, addr, data):
        addr = int(addr)
        data = int(data)
        self.data_memory.write(addr, data)
        mem_trans = MemTransaction(False, addr, data)
        self.log_data_write(mem_trans)
        self.default_data_write_cb(mem_trans)

    def execute_instruction(self, fetch_override=None):
        fetched_instruction = self.fetch_instruction(self.pc) if fetch_override is None else fetch_override
        self.prev_instr = fetched_instruction
        self.pc += 1
        self.oreg |= (fetched_instruction & 0xf)
        self.all_instructions.append(fetched_instruction)
        instr = (fetched_instruction >> 4) & 0xf
        if (instr == InstrEncoding.LDAM):
            self.areg = self.data_read(self.oreg)
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.LDBM):
            self.breg = self.data_read(self.oreg)
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.STAM):
            self.data_write(self.oreg, self.areg)
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.LDAC):
            self.areg = self.oreg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.LDBC):
            self.breg = self.oreg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.LDAP):
            self.areg = self.pc + self.oreg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.LDAI):
            self.areg = self.data_read(self.areg + self.oreg)
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.LDBI):
            self.breg = self.data_read(self.breg + self.oreg)
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.STAI):
            self.data_write(self.breg + self.oreg, self.areg)
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.BR):
            finished = self.oreg == 0xfe
            self.pc += self.oreg
            self.oreg = Reg(0)
            return finished
        elif (instr == InstrEncoding.BRZ):
            if self.areg == Reg(0):
                self.pc += self.oreg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.BRN):
            if self.areg > 127:
                self.pc += self.oreg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.BRB):
            self.pc = self.breg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.ADD):
            self.areg += self.breg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.SUB):
            self.areg -= self.breg
            self.oreg = Reg(0)
        elif (instr == InstrEncoding.PFIX):
            self.oreg = self.oreg << 4
        return False

    def execute_program(self):
        self.reset()
        exit = False
        MAX_LOOP = 100000000
        loop = 0
        while not exit and loop < MAX_LOOP:
            exit = self.execute_instruction()
            loop += 1
        if loop == MAX_LOOP:
            raise RuntimeError("MAX_LOOP exceeded!! Model failed to finish. Your code should end with instructions 0xff, 0x9e.")
