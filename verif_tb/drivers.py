import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb_bus.drivers import BusDriver
from transactions import MemTransaction

class InstructionMemoryDriver(BusDriver):
    _signals = ["i_instr_rd_data"]
    def __init__(self, entity, clock):
        super().__init__(entity, None, clock)

    def set_sig(self, ident, val):
        getattr(self.bus, ident).value = val

    async def _driver_send(self, transaction : MemTransaction, sync, **kwargs):
        await RisingEdge(self.clock)
        self.set_sig("i_instr_rd_data", transaction.data)


class DataMemoryDriver(BusDriver):
    _signals = ["i_data_rd_data"]

    def __init__(self, entity, clock):
        super().__init__(entity, None, clock)

    def set_sig(self, ident, val):
        getattr(self.bus, ident).value = val

    async def _driver_send(self, transaction : MemTransaction, sync, **kwargs):
        await RisingEdge(self.clock)
        self.set_sig("i_data_rd_data", transaction.data)

class ResetDriver(BusDriver):
    _signals = ["i_rst"]

    def __init__(self, entity, clock):
        super().__init__(entity, None, clock)

    @cocotb.coroutine
    async def reset(self):
        self.bus.i_rst.value = 1
        await ClockCycles(self.clock, 2)
        self.bus.i_rst.value = 0
        await RisingEdge(self.clock)
