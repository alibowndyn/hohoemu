#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>

#include "utils.h"



int is_valid_filename(const char *filename)
{
    size_t len = strlen(filename);

    if (len < 3 || len > MAX_FILENAME_LEN)
        return 0;

    if (strcmp(filename + len - 2, ".s") != 0)
        return 0;

    for (size_t i = 0; i < len - 2; i++)
    {
        if ( !isalnum(filename[i]) && filename[i] != '_' && filename[i] != '-' )
            return 0;
    }

    return 1;
}

uint8_t hex_to_byte(const char *hex)
{
    return (uint8_t)strtoul(hex, NULL, 16);
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