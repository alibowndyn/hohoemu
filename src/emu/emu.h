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

// Registers
static const int x86_64_registers[] = {
    UC_X86_REG_RAX,    UC_X86_REG_EAX,    UC_X86_REG_AX,   UC_X86_REG_AH,   UC_X86_REG_AL,
    UC_X86_REG_RBX,    UC_X86_REG_EBX,    UC_X86_REG_BX,   UC_X86_REG_BH,   UC_X86_REG_BL,
    UC_X86_REG_RCX,    UC_X86_REG_ECX,    UC_X86_REG_CX,   UC_X86_REG_CH,   UC_X86_REG_CL,
    UC_X86_REG_RDX,    UC_X86_REG_EDX,    UC_X86_REG_DX,   UC_X86_REG_DH,   UC_X86_REG_DL,
    UC_X86_REG_RSI,    UC_X86_REG_ESI,    UC_X86_REG_SI,   UC_X86_REG_SIL,
    UC_X86_REG_RDI,    UC_X86_REG_EDI,    UC_X86_REG_DI,   UC_X86_REG_DIL,
    UC_X86_REG_R8,     UC_X86_REG_R8D,    UC_X86_REG_R8W,  UC_X86_REG_R8B,
    UC_X86_REG_R9,     UC_X86_REG_R9D,    UC_X86_REG_R9W,  UC_X86_REG_R9B,
    UC_X86_REG_R10,    UC_X86_REG_R10D,   UC_X86_REG_R10W, UC_X86_REG_R10B,
    UC_X86_REG_R11,    UC_X86_REG_R11D,   UC_X86_REG_R11W, UC_X86_REG_R11B,
    UC_X86_REG_R12,    UC_X86_REG_R12D,   UC_X86_REG_R12W, UC_X86_REG_R12B,
    UC_X86_REG_R13,    UC_X86_REG_R13D,   UC_X86_REG_R13W, UC_X86_REG_R13B,
    UC_X86_REG_R14,    UC_X86_REG_R14D,   UC_X86_REG_R14W, UC_X86_REG_R14B,
    UC_X86_REG_R15,    UC_X86_REG_R15D,   UC_X86_REG_R15W, UC_X86_REG_R15B,
    UC_X86_REG_RIP,    UC_X86_REG_EIP,    UC_X86_REG_IP,
    UC_X86_REG_RSP,    UC_X86_REG_ESP,    UC_X86_REG_SP,   UC_X86_REG_SPL,
    UC_X86_REG_RBP,    UC_X86_REG_EBP,    UC_X86_REG_BP,   UC_X86_REG_BPL,
    UC_X86_REG_RFLAGS, UC_X86_REG_EFLAGS, UC_X86_REG_FLAGS,
    UC_X86_REG_CS,     UC_X86_REG_DS,     UC_X86_REG_SS,   UC_X86_REG_ES,   UC_X86_REG_FS, UC_X86_REG_GS,
};

#define NUM_OF_REGISTERS_TO_READ    ( (int)(sizeof(x86_64_registers) / sizeof(int)) )
static uint64_t reg_contents[NUM_OF_REGISTERS_TO_READ];

#define REG_RAX     reg_contents[0]
#define REG_RIP     reg_contents[60]
#define REG_RSP     reg_contents[63]



void init_emu(struct MemoryLayout *memory_layout, int *instruction_count);

int emulate(struct TextSegment *text_segment);





#endif
