#ifndef _EMU_EMU_H
#define _EMU_EMU_H

#include "include/unicorn/unicorn.h"
#include "utils.h"


// Memory alignment and configuration
#define UC_MEM_ALIGN_SIZE     ( 4096 )                 // Minimum memory alignment size for Unicorn Engine's `uc_mem_map` fucnction: 4kB
#define X86_MEMORY_PAGE_SIZE  ( 4096 )                 // Minimum memory page size for the x86-64 architecture: 4kB
#define CODE_START_ADDR       ( (uint64_t)0x400000 )   // Code start address: 0x400000 (4194304)

// Stack configuration
#define STACK_SIZE            ( (uint64_t)(X86_MEMORY_PAGE_SIZE) )           // Stack size: 4kB [the limit seems to be 220kb (1024*220)]
#define STACK_BYTES_TO_WRITE  ( (uint8_t)128 )                               // Number of bytes to write to the output file from the stack
#define STACK_START_ADDR      ( 0x440000 )                                   // Stack start address: 0x440000 (4456448)
#define STACK_CANARY          ( 0x0B5E55EDDEADBEEF )                         // Stack canary value: `obsessed dead beef`
#define STACK_CANARY_ADDR     ( STACK_START_ADDR - 8 )                       // Address of the stack canary: 0x43fff8 (4456440)
#define STACK_END_ADDR        ( (size_t)(STACK_START_ADDR - STACK_SIZE) )    // Stack end address: 0x43f000 (4452352)

// Instruction constants
#define RET_INSN_BYTECODE     ( 0xc3 )                  // Bytecode for the `ret` instruction



void init_emu(struct MemoryLayout *memory_layout, int *instruction_count);

int emulate(struct TextSegment *text_segment);





#endif
