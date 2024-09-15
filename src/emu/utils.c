#include <stdlib.h>
#include <stdint.h>

#include "utils.h"



uint8_t convert_ascii_hex_to_dec(char c)
{
    if (c >= 'a' && c <= 'f')
        return (uint8_t)(15 - ('f' - c));

    return (uint8_t)atoi(&c);
}

int index_of_memory_address(uint64_t *addresses, int size, uint64_t address)
{
    for (int i = 0; i < size; i++)
    {
        if (addresses[i] == address)
            return i;
    }

    return -1;
}