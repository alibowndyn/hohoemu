#ifndef _EMU_UTILS
#define _EMU_UTILS

#include <stdint.h>



struct MemorySegment
{
    uint64_t addr;
    uint8_t *bytes;
    uint64_t size;
};

struct TextSegment
{
    struct MemorySegment seg;
    uint64_t main_addr;
};

struct MemoryLayout
{
    struct TextSegment text;
    struct MemorySegment rodata;
    struct MemorySegment data;
    struct MemorySegment bss;
    uint64_t memory_start_addr;
    uint64_t memory_end_addr;
};

struct AssemblyText
{
    char **lines;
    uint64_t *addresses;
    int num_lines;
};



uint8_t convert_ascii_hex_to_dec(char c);

int index_of_memory_address(uint64_t *addresses, int size, uint64_t address);




#endif