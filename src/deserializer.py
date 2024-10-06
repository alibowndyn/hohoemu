from emu_dataclasses import *
from utils import *



class Deserializer():
    '''A class that deserializes the output of the emulator.'''

    _input: str
    '''The input string to be deserialized.'''
    _program: ExecutedProgram
    '''The deserialized `ExecutedProgram`.'''


    def __init__(self):
        self._program = create_empty_executed_program()


    def get_executed_program(self) -> ExecutedProgram:
        '''Returns the deserialized `ExecutedProgram`.'''

        self._program = create_empty_executed_program()
        self._input = open('/tmp/emu_output_240830.txt', 'r').read()

        return self.parse_input_file()

    def parse_input_file(self) -> ExecutedProgram:
        '''Parses the input file and returns an `ExecutedProgram`.'''

        parts = self._input.split('\n><\n')

        self.deserialize_assembly(parts[0])

        self.deserialize_mem_layout_and_static_segments(parts[1])

        self.deserialize_insns_execution_contexts(parts[2:])

        return self._program

    def deserialize_assembly(self, str: str) -> None:
        '''Deserializes the assembly code from the given string.'''

        lines = str.split('\n')
        instructions = []
        addresses = []

        for line in lines:
            addresses.append(int(line[:7]))
            instructions.append(line[7:].rstrip())

        self._program.code = AssemblyCode(instructions, addresses, len(instructions))

    def deserialize_mem_layout_and_static_segments(self, str: str) -> None:
        '''Deserializes the memory layout and the static segments from the given string.'''

        lines = str.split('\n')

        self._program.mem_layout = MemoryLayout(*map(int, lines[:4]))

        text_data = list(map(int, lines[5].split(' ')))
        rodata_data = list(map(int, lines[6].split(' ')))

        # read the symbols in the rodata segment
        rodata_symbols: list[Symbol] = []
        for line in lines[7:]:
            parts = line.split(' ')
            sym_bytes = list(map(int, parts[2:]))
            rodata_symbols.append(Symbol(parts[1], int(parts[0]), len(sym_bytes), sym_bytes))

        # remove irrelevant symbols from the rodata segment
        rodata_symbols = [sym for sym in rodata_symbols if sym.name not in irrelevant_symbols]

        self._program.static_mem = StaticMemory(
            text=TextSegment(
                name='text',
                main_addr=int(lines[4]),
                addr=text_data[0],
                size=text_data[1],
                bytes=text_data[3:],
                num_symbols=text_data[2],
                symbols=[]),
            rodata=MemorySegment(
                name='rodata',
                addr=rodata_data[0],
                size=rodata_data[1],
                bytes=text_data[3:],
                num_symbols=rodata_data[2],
                symbols=rodata_symbols))

    def deserialize_insns_execution_contexts(self, contexts: list) -> None:
        '''Deserializes the execution contexts from the given string.'''

        for ctx in contexts:
            lines = ctx.split('\n')

            context = create_empty_execution_context()
            context.has_program_ended = False

            line_parts = lines[0].split(' ')
            if (line_parts[0][0] == '#'):
                self._program.contexts.append(context)
                self._program.ex_info.has_stack_overflowed = 1
                self._program.ex_info.addr = int(line_parts[1])
                return


            reg_values = list(map(int, line_parts))
            rdict = {k : v for k, v in zip(list(Registers.__dataclass_fields__.keys())[:-1], reg_values)}
            context.regs = Registers(*reg_values, rdict)

            context.stack.content.extend(map(int, lines[1].split(' ')))


            data_data = list(map(int, lines[2].split(' ')))
            bss_data = list(map(int, lines[3].split(' ')))

            # read the symbols in the data segment
            data_symbols: list[Symbol] = []
            for line in lines[5:5+data_data[2]]:
                parts = line.split(' ')
                sym_bytes = list(map(int, parts[2:]))
                data_symbols.append(Symbol(parts[1], int(parts[0]), len(sym_bytes), sym_bytes))

            # remove irrelevant symbols from the data segment
            data_symbols = [sym for sym in data_symbols if sym.name not in irrelevant_symbols]

            # read the symbols in the bss segment
            bss_symbols: list[Symbol] = []
            for line in lines[5+data_data[2]:5+data_data[2]+bss_data[2]]:
                parts = line.split(' ')
                sym_bytes = list(map(int, parts[2:]))
                bss_symbols.append(Symbol(parts[1], int(parts[0]), len(sym_bytes), sym_bytes))

            # remove irrelevant symbols from the bss segment
            bss_symbols = [sym for sym in bss_symbols if sym.name not in irrelevant_symbols]

            context.dynamic_mem = DynamicMemory(
                    data=MemorySegment(
                        name='data',
                        addr=data_data[0],
                        size=data_data[1],
                        bytes=data_data[3:],
                        num_symbols=data_data[2],
                        symbols=data_symbols),
                    bss=MemorySegment(
                        name='bss',
                        addr=bss_data[0],
                        size=bss_data[1],
                        bytes=bss_data[3:],
                        num_symbols=bss_data[2],
                        symbols=bss_symbols))

            # read the current instruction
            insn_data = list(map(int, lines[4].split(' ')))
            context.insn = Instruction(
                    index=insn_data[0],
                    text=self._program.code.lines[insn_data[0]],
                    addr=insn_data[1],
                    size=insn_data[2],
                    bytecode=insn_data[2:])

            if len(lines) == 6 and lines[5] == '@__@':
                self._program.ex_info.is_rsp_invalid = 1

            self._program.contexts.append(context)

        # indicate that the program has ended after the last context
        self._program.contexts[-1].has_program_ended = True
