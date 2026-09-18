from collections import namedtuple

MemTransactionBase = namedtuple("MemTransaction", "is_read addr data")

class MemTransaction(MemTransactionBase):
    def __str__(self):
        type_str = "<-" if self.is_read else "->"
        data_str = "?" if self.data is None else f"0x{self.data:02x}"
        return f"{data_str} {type_str} mem[0x{self.addr:02x}]"

    def __repr__(self):
        return self.__str__()