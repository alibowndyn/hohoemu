#include <stdio.h>

#include "utils.h"
#include "serializer.h"


extern struct AssemblyText assembly;
FILE *emu_out_fp;


#define PRINT_TO_FILE(format_str, ...)     \
    fprintf(emu_out_fp, format_str, ##__VA_ARGS__);



static void print_segment(struct MemorySegment *seg)
{
    PRINT_TO_FILE("%ld %ld ", seg->addr, seg->size)

    for (uint32_t i = 0; i < seg->size; i++)
    {
        PRINT_TO_FILE("%d%s", seg->bytes[i], (i == seg->size-1) ? "" : " ")
    }

    PRINT_TO_FILE("\n")
}

void initialize_serializer()
{
    emu_out_fp = fopen("/tmp/emu_output_240830.txt", "w");
}

void write_separator()
{
    PRINT_TO_FILE("><\n")
}

void write_memory_layout(struct MemoryLayout *mem, uint64_t stack_start_addr, uint64_t stack_end_addr, int write_static_content)
{
    if (write_static_content)
    {
        PRINT_TO_FILE("%ld\n%ld\n%ld\n%ld\n%ld\n",
            mem->memory_start_addr, mem->memory_end_addr, stack_start_addr, stack_end_addr, mem->text.main_addr);

        print_segment(&mem->text.seg);
        print_segment(&mem->rodata);

        write_separator();
    }
    else
    {
        print_segment(&mem->data);
        print_segment(&mem->bss);
    }
}

void write_assembly_instructions_and_addresses(struct AssemblyText *assembly)
{
    for (int i = 0; i < assembly->num_lines; i++)
    {
        PRINT_TO_FILE("%ld%s\n", assembly->addresses[i], assembly->lines[i])
    }

    write_separator();
}

void write_instruction_info(int index, uint32_t size, __uint128_t bytecode)
{
    PRINT_TO_FILE("%d %u ", index, size);

    for (uint32_t i = 0; i < size; i++)
    {
        PRINT_TO_FILE("%d%s", (uint32_t)((bytecode >> (i * 8)) & 0xff), (i == size-1) ? "" : " ");
    }

    PRINT_TO_FILE("\n")
}

void write_registers(int size, uint64_t *registers)
{
    for (int i = 0; i < size; i++)
    {
        PRINT_TO_FILE("%ld%s", registers[i], (i == size-1) ? "" : " ")
    }

    PRINT_TO_FILE("\n");
}

void write_stack_content(int size, uint8_t *bytes)
{
    for (int i = 0; i < size; i++)
    {
        PRINT_TO_FILE("%d%s", bytes[i], (i == size-1) ? "" : " ")
    }

    PRINT_TO_FILE("\n");
}

void write_stack_overflow_info(uint64_t addr)
{
    PRINT_TO_FILE("#__# %ld", addr)
}

void write_invalid_stack_pointer_value_indicator()
{
    PRINT_TO_FILE("@__@")
}

void destroy_serializer()
{
    fclose(emu_out_fp);
}
