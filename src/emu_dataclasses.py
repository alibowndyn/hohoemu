from dataclasses import dataclass



@dataclass
class AssemblyCode:
    lines: list[str]
    addresses: list[int]
    num_lines: int

@dataclass
class MemoryLayout:
    text_start_addr: int
    bss_end_addr: int
    stack_start_addr: int
    stack_end_addr: int

@dataclass
class MemorySegment:
    addr: int
    size: int
    bytes: list[int]

@dataclass
class TextSegment(MemorySegment):
    main_addr: int

@dataclass
class StaticMemory:
    text: TextSegment
    rodata: MemorySegment

@dataclass
class DynamicMemory:
    data: MemorySegment
    bss: MemorySegment

@dataclass
class Instruction:
    index: int
    text: str
    addr: int
    size: int
    bytecode: list[int]

@dataclass
class Registers:
    RAX: int
    RBX: int
    RCX: int
    RDX: int
    RFLAGS: int
    RIP: int
    RSP: int
    RBP: int
    RDI: int
    RSI: int
    R8: int
    R9: int
    R10: int
    R11: int
    R12: int
    R13: int
    R14: int
    R15: int

    rdict: dict[str, int]

@dataclass
class Stack:
    content: list[int]

@dataclass
class ExecutionContext:
    insn: Instruction
    dynamic_mem: DynamicMemory
    regs: Registers
    stack: Stack

@dataclass
class RuntimeExceptionInfo:
    index: int
    has_stack_overflowed: bool
    addr: int
    is_rsp_invalid: bool

@dataclass
class ExecutedProgram:
    code: AssemblyCode
    mem_layout: MemoryLayout
    static_mem: StaticMemory
    contexts: list[ExecutionContext]
    ex_info: RuntimeExceptionInfo


def create_empty_executed_program() -> ExecutedProgram:
    return ExecutedProgram(
        code=AssemblyCode(lines=[], addresses=[], num_lines=0),
        mem_layout=MemoryLayout(
            text_start_addr=0, bss_end_addr=0,
            stack_start_addr=0, stack_end_addr=0),
        static_mem=StaticMemory(
            text=TextSegment(main_addr=0, addr=0, size=0, bytes=[]),
            rodata=MemorySegment(addr=0, size=0, bytes=[])),
        contexts=[],
        ex_info=RuntimeExceptionInfo(index=0, has_stack_overflowed=0, addr=0, is_rsp_invalid=0))

def create_empty_execution_context() -> ExecutionContext:
    return ExecutionContext(
            insn=Instruction(index=0, text='', addr=0, size=0, bytecode=[]),
            dynamic_mem=DynamicMemory(
                data=MemorySegment(addr=0, size=0, bytes=[]),
                bss=MemorySegment(addr=0, size=0, bytes=[])),
            regs=[],
            stack=Stack(content=[]))
