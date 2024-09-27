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
class Symbol:
    name: str
    addr: int
    size: int
    bytes: list[int]

@dataclass
class MemorySegment:
    name: str
    addr: int
    size: int
    bytes: list[int]
    num_symbols: int
    symbols: list[Symbol]

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
    EAX: int
    AX: int
    AH: int
    AL: int

    RBX: int
    EBX: int
    BX: int
    BH: int
    BL: int

    RCX: int
    ECX: int
    CX: int
    CH: int
    CL: int

    RDX: int
    EDX: int
    DX: int
    DH: int
    DL: int

    RSI: int
    ESI: int
    SI: int
    SIL: int

    RDI: int
    EDI: int
    DI: int
    DIL: int

    R8: int
    R8D: int
    R8W: int
    R8B: int

    R9: int
    R9D: int
    R9W: int
    R9B: int

    R10: int
    R10D: int
    R10W: int
    R10B: int

    R11: int
    R11D: int
    R11W: int
    R11B: int

    R12: int
    R12D: int
    R12W: int
    R12B: int

    R13: int
    R13D: int
    R13W: int
    R13B: int

    R14: int
    R14D: int
    R14W: int
    R14B: int

    R15: int
    R15D: int
    R15W: int
    R15B: int

    RIP: int
    EIP: int
    IP: int

    RSP: int
    ESP: int
    SP: int
    SPL: int

    RBP: int
    EBP: int
    BP: int
    BPL: int

    RFLAGS: int
    EFLAGS: int
    FLAGS: int

    CS: int
    DS: int
    SS: int
    ES: int
    FS: int
    GS: int

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
            text=TextSegment(main_addr=0, name='text', addr=0, size=0, bytes=[], num_symbols=0, symbols=[]),
            rodata=MemorySegment(name='rodata', addr=0, size=0, bytes=[], num_symbols=0, symbols=[])),
        contexts=[],
        ex_info=RuntimeExceptionInfo(index=0, has_stack_overflowed=0, addr=0, is_rsp_invalid=0))

def create_empty_execution_context() -> ExecutionContext:
    return ExecutionContext(
            insn=Instruction(index=0, text='', addr=0, size=0, bytecode=[]),
            dynamic_mem=DynamicMemory(
                data=MemorySegment(name='data', addr=0, size=0, bytes=[], num_symbols=0, symbols=[]),
                bss=MemorySegment(name='bss', addr=0, size=0, bytes=[], num_symbols=0, symbols=[])),
            regs=[],
            stack=Stack(content=[]))


main_regs = [
    'RAX', 'RBX', 'RCX', 'RDX', 'RSI', 'RDI',
    'R8', 'R9', 'R10', 'R11', 'R12', 'R13',
    'R14', 'R15', 'RIP', 'RBP', 'RSP', 'RFLAGS',
#   'CS', 'DS', 'SS', 'ES', 'FS', 'GS'
]

flags = ['CF', 'PF', 'ZF', 'SF', 'OF']

reg_subparts = {
    'RAX': ['EAX', 'AX', 'AH', 'AL'],
    'RBX': ['EBX', 'BX', 'BH', 'BL'],
    'RCX': ['ECX', 'CX', 'CH', 'CL'],
    'RDX': ['EDX', 'DX', 'DH', 'DL'],
    'RSI': ['ESI', 'SI', 'SIL'],
    'RDI': ['EDI', 'DI', 'DIL'],
    'R8':  ['R8D', 'R8W', 'R8B'],
    'R9':  ['R9D', 'R9W', 'R9B'],
    'R10': ['R10D', 'R10W', 'R10B'],
    'R11': ['R11D', 'R11W', 'R11B'],
    'R12': ['R12D', 'R12W', 'R12B'],
    'R13': ['R13D', 'R13W', 'R13B'],
    'R14': ['R14D', 'R14W', 'R14B'],
    'R15': ['R15D', 'R15W', 'R15B'],
    'RIP': ['EIP', 'IP'],
    'RSP': ['ESP', 'SP', 'SPL'],
    'RBP': ['EBP', 'BP', 'BPL'],
    'RFLAGS': flags,
    'CS': [],
    'DS': [],
    'SS': [],
    'ES': [],
    'FS': [],
    'GS': []
}

def extract_rflag_bits(rflags, flag):
    match flag:
        case 'CF':
            return (rflags >> 0) & 1    # Carry Flag
        case 'PF':
            return (rflags >> 2) & 1    # Parity Flag
        case 'ZF':
            return (rflags >> 6) & 1    # Zero Flag
        case 'SF':
            return (rflags >> 7) & 1    # Sign Flag
        case 'OF':
            return (rflags >> 11) & 1   # Overflow Flag

irrelevant_symbols = ['_IO_stdin_used', '__data_start', '__dso_handle', 'completed.0']