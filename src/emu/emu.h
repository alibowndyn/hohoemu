#ifndef _EMU_EMU
#define _EMU_EMU

#include "include/unicorn/unicorn.h"
#include "utils.h"


#define UC_MEM_ALIGN_SIZE     ( 4 * 1024 )              // 4kB (4096)
#define CODE_START_ADDR       ( (uint64_t)0x400000 )    // dec: 4194304

#define X86_MEMORY_PAGE_SIZE  ( 4096 )
#define STACK_SIZE            ( (uint64_t)(X86_MEMORY_PAGE_SIZE) )           // 4kB (dec: 4096) (the limit seems to be 220kb (1024*220))
#define STACK_BYTES_TO_WRITE  ( (uint8_t)128 )                               // Number of bytes to write to the output file from the stack
#define STACK_START_ADDR      ( 0x440000 )                                   // Highest address of the stack (dec: 4456448)
#define STACK_CANARY          ( 0x0B5E55EDDEADBEEF )                         // "obsessed dead beef"
#define STACK_CANARY_ADDR     ( STACK_START_ADDR - 8 )                       // 0x43fff8 (dec: 4456440)
#define STACK_END_ADDR        ( (size_t)(STACK_START_ADDR - STACK_SIZE) )    // Lowest address of the stack (hex: 0x43c000 | dec: 4440064))

#define RET_INSN_BYTECODE     ( 0xc3 )


void init_emu(struct MemoryLayout *memory_layout, int *instruction_count);

void print_mapped_memory_regions();

int emulate(struct TextSegment *text_segment);





#endif
