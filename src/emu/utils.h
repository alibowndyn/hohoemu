#ifndef _EMU_UTILS_H
#define _EMU_UTILS_H

#include <stdint.h>


#define COMPILED_FILE_PATH   "/tmp/compiled_assembly_file"
#define SERIALIZED_OUTPUT_PATH  "/tmp/emu_output_240830.txt"
#define MAX_FILENAME_LEN 255


struct Symbol
{
    char *name;
    uint64_t addr;
    uint64_t size;
    uint8_t *bytes;
};

struct MemorySegment
{
    uint64_t addr;
    uint64_t size;
    uint8_t *bytes;
    uint16_t num_symbols;
    struct Symbol **symbols;
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


/**
 * @brief Checks if a given filename is valid.
 *
 * This function verifies that the provided filename meets certain criteria:
 *
 * - The filename must be between 3 and MAX_FILENAME_LEN characters long.
 *
 * - The filename must end with the suffix ".s".
 *
 * - All characters in the filename (excluding the last two for the suffix)
 *   must be alphanumeric, an underscore (_), or a hyphen (-).
 *
 * @param filename A pointer to a null-terminated string representing the
 *                 filename to be validated.
 *
 * @return 1 if the filename is valid, 0 otherwise.
 */
int is_valid_filename(const char* filename);

/**
 * @brief Converts a hexadecimal string to a byte.
 *
 * This function takes a null-terminated string representing a hexadecimal
 * number and converts it to an 8-bit unsigned integer (byte). The input
 * string should represent a valid hexadecimal value (e.g., "1A", "FF").
 *
 * @param hex A pointer to a null-terminated string containing the hexadecimal
 *            representation to be converted.
 *
 * @return The converted byte value as an 8-bit unsigned integer. If the
 *         hexadecimal value exceeds the range of a byte (0x00 to 0xFF),
 *         it is truncated to fit within this range.
 */
uint8_t hex_to_byte(const char *hex);

/**
 * @brief Finds the index of a specified memory address in an array.
 *
 * @param addresses A pointer to an array of addresses to search.
 * @param size The number of elements in the `addresses` array.
 * @param address The memory address to find in the array.
 *
 * @return The index of the first occurrence of the specified address
 *         in the array, or -1 if the address is not found.
 */
int index_of_memory_address(uint64_t *addresses, int size, uint64_t address);





#endif