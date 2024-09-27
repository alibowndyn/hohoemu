#ifndef _EMU_SERIALIZER_H
#define _EMU_SERIALIZER_H

#include "utils.h"



void initialize_serializer();

void write_separator();

void write_memory_layout(struct MemoryLayout *mem, uint64_t stack_start_addr, uint64_t stack_end_addr, int write_static_content);

void write_assembly_instructions_and_addresses(struct AssemblyText *assembly);

void write_instruction_info(int index, uint32_t size, __uint128_t bytecode);

void write_symbol_info(struct Symbol *symbol);

void write_registers(int size, uint64_t *registers);

void write_stack_content(int size, uint8_t *bytes);

void write_stack_overflow_info(uint64_t addr);

void write_invalid_stack_pointer_value_indicator();

void destroy_serializer();





#endif
