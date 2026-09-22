import array
class MemoryModel:
    def __init__(self, mem_depth=256, mem_width=8):
        self.mem_depth = mem_depth
        self.memory = array.array('B', (0 for _ in range(mem_depth)))

    def write(self, addr, data):
        self.memory[addr] = data

    def read(self, addr):
        return self.memory[addr]

    def block_write(self, start_addr, data_block):
        """Use to initialise memory."""
        print(len(data_block))
        print(start_addr)
        print(self.mem_depth)
        assert len(data_block) - start_addr <= self.mem_depth
        for i, data in enumerate(data_block):
            self.memory[start_addr + i] = data