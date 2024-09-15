from emu_dataclasses import *


class Deserializer():
    _input: str
    _program: ExecutedProgram

    def __init__(self):
        self._program = create_empty_executed_program()

    def get_executed_program(self) -> ExecutedProgram:
        self._program = create_empty_executed_program()
        self._input = open("/tmp/emu_output_240830.txt", "r").read()
        return self.parse_input_file()

    def parse_input_file(self) -> ExecutedProgram:
        parts = self._input.split('\n><\n')

        self.deserialize_assembly(parts[0])

        self.deserialize_mem_layout_and_static_segments(parts[1])

        self.deserialize_insns_execution_contexts(parts[2:])


        return self._program

    def deserialize_assembly(self, str: str) -> None:
        lines = str.split('\n')
        instructions = []
        addresses = []

        for line in lines:
            addresses.append(int(line[:7]))
            instructions.append(line[7:].rstrip())

        self._program.code = AssemblyCode(instructions, addresses, len(instructions))

    def deserialize_mem_layout_and_static_segments(self, str: str) -> None:
        lines = str.split('\n')

        self._program.mem_layout = MemoryLayout(*map(int, lines[:4]))


        text_data = list(map(int, lines[5].split(' ')))
        rodata_data = list(map(int, lines[6].split(' ')))

        self._program.static_mem = StaticMemory(
            text=TextSegment(
                main_addr=int(lines[4]),
                addr=text_data[0],
                size=text_data[1],
                bytes=text_data[2:]),
            rodata=MemorySegment(
                addr=rodata_data[0],
                size=rodata_data[1],
                bytes=rodata_data[2:]))

    def deserialize_insns_execution_contexts(self, contexts: list) -> None:
        for c in contexts:
            lines = c.split('\n')

            context = create_empty_execution_context()

            line_parts = lines[0].split(' ')
            print(line_parts)
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
            context.dynamic_mem = DynamicMemory(
                    data=MemorySegment(
                        addr=data_data[0],
                        size=data_data[1],
                        bytes=data_data[2:]),
                    bss=MemorySegment(
                        addr=bss_data[0],
                        size=bss_data[1],
                        bytes=bss_data[2:]))

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
