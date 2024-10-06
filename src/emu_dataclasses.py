from dataclasses import dataclass



@dataclass
class AssemblyCode:
    '''A representation of the assembly code of a program.'''

    lines: list[str]
    '''The lines of the assembly code.'''
    addresses: list[int]
    '''The addresses of the instructions.'''
    num_lines: int
    '''The number of lines in the assembly code.'''

@dataclass
class MemoryLayout:
    '''A representation of the memory layout of a program.'''

    text_start_addr: int
    '''The starting address of the .text segment.'''
    bss_end_addr: int
    '''The ending address of the .bss segment.'''
    stack_start_addr: int
    '''The starting address of the stack.'''
    stack_end_addr: int
    '''The ending address of the stack.'''

@dataclass
class Symbol:
    '''A representation of a static data symbol.'''

    name: str
    '''The name of the symbol.'''
    addr: int
    '''The starting address of the symbol.'''
    size: int
    '''The size of the symbol in bytes.'''
    bytes: list[int]
    '''The content of the symbol.'''

@dataclass
class MemorySegment:
    '''A representation of a memory segment.'''

    name: str
    '''The name of the memory segment.'''
    addr: int
    '''The starting address of the memory segment.'''
    size: int
    '''The size of the memory segment in bytes.'''
    bytes: list[int]
    '''The content of the memory segment.'''
    num_symbols: int
    '''The number of symbols in the memory segment.'''
    symbols: list[Symbol]
    '''The symbols in the memory segment.'''

@dataclass
class TextSegment(MemorySegment):
    '''A representation of the .text segment of a program.'''

    main_addr: int
    '''The address of the main function.'''

@dataclass
class StaticMemory:
    '''A representation of the static memory of a program.'''

    text: TextSegment
    '''The .text segment of the program.'''
    rodata: MemorySegment
    '''The .rodata segment of the program.'''

@dataclass
class DynamicMemory:
    '''A representation of the dynamic memory of a program.'''

    data: MemorySegment
    '''The .data segment of the program.'''
    bss: MemorySegment
    '''The .bss segment of the program.'''

@dataclass
class Instruction:
    '''A representation of an instruction.'''
    index: int
    '''The index of the current instruction in the list of execution contexts.'''
    text: str
    '''The text of the instruction.'''
    addr: int
    '''The starting address of the instruction in the .text segment.'''
    size: int
    '''The size of the instruction in bytes.'''
    bytecode: list[int]
    '''The bytecode of the instruction.'''

@dataclass
class Registers:
    '''A representation of the registers.'''

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

    RBP: int
    EBP: int
    BP: int
    BPL: int

    RSP: int
    ESP: int
    SP: int
    SPL: int

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
    '''A representation of the stack.'''

    content: list[int]
    '''The content of the stack.'''

@dataclass
class ExecutionContext:
    '''A representation of the state of a program at a given point in time.'''

    insn: Instruction
    '''The current instruction.'''
    dynamic_mem: DynamicMemory
    '''The state of the dynamic memory.'''
    regs: Registers
    '''The current state of the registers.'''
    stack: Stack
    '''The current state of the stack.'''
    has_program_ended: bool
    '''Whether the program has ended.'''

@dataclass
class RuntimeExceptionInfo:
    '''A representation of the information about a runtime exception.'''

    index: int
    '''The index of the context where the exception occurred.'''
    has_stack_overflowed: bool
    '''Whether the stack has overflowed.'''
    addr: int
    '''The value stored in the stack pointer.'''
    is_rsp_invalid: bool
    '''Whether the stack pointer contains an invalid value.'''

@dataclass
class ExecutedProgram:
    '''A representation of a program that has been executed.'''

    index: int
    '''The index of the current context in the list of execution contexts.'''
    code: AssemblyCode
    '''The assembly code of the program.'''
    mem_layout: MemoryLayout
    '''The memory layout of the program.'''
    static_mem: StaticMemory
    '''The static memory of the program.'''
    contexts: list[ExecutionContext]
    '''The execution contexts of the program.'''
    ex_info: RuntimeExceptionInfo
    '''Information about a runtime exception.'''


    def step(self, direction: int) -> int:
        ''' Moves the instruction counter by `direction` steps.

            Returns: 0 if the instruction counter is within bounds,
                     1 if the instruction counter is at the beginning and
                     2 if the instruction counter is at the end.'''

        self.index += direction

        if self.index >= len(self.contexts):
            self.index = len(self.contexts) - 1
            return 2

        if self.index < 0:
            self.index = 0
            return 1

        return 0

    def get_current_context(self) -> ExecutionContext:
        '''Returns the current execution context.'''

        return self.contexts[self.index]

    def get_flag(self, flag) -> int:
        '''Extracts the specified flag from the RFLAGS register.'''

        rflags = self.get_current_context().regs.RFLAGS
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


def create_empty_executed_program() -> ExecutedProgram:
    '''Creates an empty `ExecutedProgram`.'''

    return ExecutedProgram(
        0,
        AssemblyCode([], [], 0),
        MemoryLayout(0, 0, 0, 0),
        StaticMemory(
            TextSegment(0, 'text', 0, 0, [], 0, []),
            MemorySegment('rodata', 0, 0, [], 0, [])),
        [],
        RuntimeExceptionInfo(0, False, 0, False))

def create_empty_execution_context() -> ExecutionContext:
    '''Creates an empty `ExecutionContext`.'''

    return ExecutionContext(
        Instruction(0, '', 0, 0, []),
        DynamicMemory(
            MemorySegment('data', 0, 0, [], 0, []),
            MemorySegment('bss', 0, 0, [], 0, [])),
        [],
        Stack([]),
        False)
