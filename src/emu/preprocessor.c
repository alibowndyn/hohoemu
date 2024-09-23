#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "preprocessor.h"
#include "utils.h"



static void process_symbol_table(FILE *fp, struct MemoryLayout *mem)
{
    char line_buf[256] = {0};

    // We are processing a line like this:
    // "0000000000401020 g     F .text	0000000000000026              _start"
    while ( fgets(line_buf, sizeof(line_buf), fp) != NULL )
    {
        if (line_buf[0] == '0')
        {
            if (mem->memory_start_addr == 0)
            {
                if ( strstr(line_buf, " _start") != NULL )
                    mem->memory_start_addr = strtoul(line_buf, NULL, 16);
            }

            if (mem->memory_end_addr == 0)
            {
                if ( strstr(line_buf, " _end") != NULL )
                    mem->memory_end_addr = strtoul(line_buf, NULL, 16);
            }

            if (mem->bss.addr == 0)
            {
                if ( strstr(line_buf, " __bss_start") != NULL )
                    mem->bss.addr = strtoul(line_buf, NULL, 16);
            }

            if (mem->text.main_addr == 0)
            {
                if ( strstr(line_buf, " main") != NULL )
                    mem->text.main_addr = strtoul(line_buf, NULL, 16);
            }
        }

        if (mem->memory_start_addr != 0 && mem->memory_end_addr != 0 &&
            mem->text.main_addr    != 0 && mem->bss.addr        != 0)
            break;
    }
}

static void process_section_content(FILE *fp, const char *read_until_str, struct MemorySegment *segment)
{
    char line_buf[256];
    char data_buf[1024];

    // We are processing a line like this:
    // " 401020 f30f1efa 31ed4989 d15e4889 e24883e4  ....1.I..^H..H.."
    while ( fgets(line_buf, sizeof(line_buf), fp) != NULL && strstr(line_buf, read_until_str) == NULL )
    {
        // valid lines all start with a space character
        if (line_buf[0] == ' ')
        {
            // only extract the segment's address on first encounter
            if (segment->addr == 0)
                segment->addr = strtoull(line_buf, NULL, 16);

            // start at 8, because we want to skip the address part of the line
            // increment i by 2 because we process two hex characters (1 byte) at a time
            for (size_t i = 8; i < strlen(line_buf); i += 2)
            {
                if (line_buf[i] == ' ')
                {
                    // if we encounter 2 space characters, we ran out of useful characters to process
                    if (line_buf[i + 1] == ' ')
                        break;

                    // jump over the space character
                    i++;
                }

                // convert the next two hex characters to a byte
                char hex[] = { line_buf[i], line_buf[i + 1], '\0' };
                data_buf[segment->size++] = hex_to_byte(hex);
            }
        }
    }

    segment->bytes = malloc(segment->size);
    memcpy(segment->bytes, data_buf, segment->size);
}

static void read_assembly_instructions(FILE *fp, struct AssemblyText *assembly)
{
    char as_lines[256][256];
    char as_line_buf[256];
    char line_buf[256];
    uint64_t as_addrs[256];
    int line_idx = 0;

    while ( fgets(line_buf, sizeof(line_buf), fp) != NULL )
    {
        if ( strstr(line_buf, "Disassembly of section .rodata:") != NULL )
            break;

        // When the two buffers contain lines like these:
        // "#         pop        rbp"
        // "  401176:	5d                   	pop    rbp"
        if (as_line_buf[0] == '#' && line_buf[0] == ' ')
        {
            // We are parsing a line like this:
            // "40110c:	push   rbp"
            sscanf(line_buf, "  %6lx", &as_addrs[line_idx]);

            // read until '#' or a newline
            // this means we won't save comments from the source code
            sscanf(as_line_buf, "#%[^#\n]", as_lines[line_idx]);
            line_idx++;
        }

        memcpy(as_line_buf, line_buf, strlen(line_buf));
    }

    assembly->num_lines = line_idx;
    assembly->addresses = malloc(sizeof(uint64_t) * assembly->num_lines);
    assembly->lines     = malloc(sizeof(char *) * assembly->num_lines);

    for (int i = 0; i < assembly->num_lines; i++)
    {
        assembly->addresses[i] = as_addrs[i];

        assembly->lines[i] = malloc(sizeof(char) * 128);
        memcpy(assembly->lines[i], as_lines[i], 128);
    }


    for (int i = 0; i < assembly->num_lines; i++)
    {
        printf("%#lx: %s\n", assembly->addresses[i], assembly->lines[i]);
    }
}

static void get_symbol_data(FILE *fp, const char *read_until_str, struct MemorySegment *segment)
{
    char line_buf[256];
    int sym_arr_size = 8;
    int sym_idx = 0; // variable keeping track of the number of symbols in the segment

    struct Symbol **syms = calloc(sym_arr_size, sizeof(struct Symbol *));
    for (int i = 0; i < sym_arr_size; i++)
    {
        syms[i] = calloc(1, sizeof(struct Symbol));
        syms[i]->name = malloc(64 + 1);
    }

    while ( fgets(line_buf, sizeof(line_buf), fp) != NULL && strstr(line_buf, read_until_str) == NULL)
    {
        // only lines starting with '0' can contain a symbol's info
        if (line_buf[0] != '0')
            continue;

        // we are trying to extract a symbol's info from a line like this:
        // "0000000000402004 <txt1>:"
        int items_processed = sscanf(line_buf, "%16lx <%[^>]", &syms[sym_idx]->addr, syms[sym_idx]->name);

        // only store a symbol if both its address and name could be read from a line
        if (items_processed == 2)
        {
            // calculate the size of the (n-1)th symbol in the segment by subtracting
            // its starting address from the starting address of the nth symbol
            if (sym_idx > 0)
            {
                struct Symbol *prev = syms[sym_idx - 1];
                struct Symbol *curr = syms[sym_idx];

                prev->size = curr->addr - prev->addr;
                prev->bytes = malloc(prev->size);

                // copy the bytes of the (n-1)th symbol from the segment's bytes
                memcpy(prev->bytes, segment->bytes + (prev->addr - segment->addr), prev->size);
            }

            sym_idx++;
        }

        if (sym_idx >= sym_arr_size)
        {
            sym_arr_size *= 2;
            syms = realloc(syms, sym_arr_size * sizeof(struct Symbol *));

            for (int i = sym_idx; i < sym_arr_size; i++)
            {
                syms[i] = calloc(1, sizeof(struct Symbol));
                syms[i]->name = malloc(64 + 1);
            }
        }
    }

    syms = realloc(syms, sym_idx * sizeof(struct Symbol *));

    segment->num_symbols = sym_idx;
    segment->symbols = syms;

    // calculate the size of the last symbol in the segment by subtracting
    // its starting address from the end address of the segment
    struct Symbol *last_symbol = segment->symbols[segment->num_symbols - 1];
    last_symbol->size = (segment->addr + segment->size) - last_symbol->addr;

    // copy the bytes of the last symbol from the segment's bytes
    last_symbol->bytes = malloc(last_symbol->size);
    memcpy(last_symbol->bytes, segment->bytes + (last_symbol->addr - segment->addr), last_symbol->size);

    for (int i = 0; i < segment->num_symbols; i++)
    {
        printf("\nSymbol's name: %s\n"\
               "Its address: %#lx\n"\
               "Its size: %ld\n", segment->symbols[i]->name, segment->symbols[i]->addr, segment->symbols[i]->size);

        for (int j = 0; j < segment->symbols[i]->size; j++)
            printf("%02x ", segment->symbols[i]->bytes[j]);

        puts("");
    }
}

void process_objdump_output(struct MemoryLayout *mem, struct AssemblyText *assembly)
{
    // objdump -sStw --source-comment --no-show-raw-insn -M"x86-64,intel" -j .text -j .bss -j .data -j .rodata sout
    FILE *obj_fp = popen(
        "/usr/bin/objdump "
        "-s "                           // display the full contents of sections
        "-S "                           // interleave source code lines with disassembly (implies -d [--disassemble])
        "-t "                           // print the symbol table entries of the file
//      "-w "                           // dont't line-wrap machine-code bytes
        "--source-comment "             // all source code lines are prefixed with `# `
        "--no-show-raw-insn "           // when disassembling instructions, do not print their bytecode
        "-M \"x86-64,intel\" "          // specify target architecture and syntax style
        "--section=.text "              // disassemble .text section
        "--section=.rodata "            // disassemble .rodata section
        "--section=.data "              // disassemble .data section
        "--section=.bss "               // disassemble .bss section
        COMPILED_FILE_PATH,             // the compiled file
        "r");

    if (obj_fp == NULL)
    {
        perror("Call to popen failed");
        exit(1);
    }


    // get the addresses of start, end, __bss_start and main symbols from the symbol table
    process_symbol_table(obj_fp, mem);

    // read contents of the TEXT segment
    process_section_content(obj_fp, "Contents of section .rodata",   &mem->text.seg);
    // read contents of the RODATA segment
    process_section_content(obj_fp, "Contents of section .data",     &mem->rodata);
    // read contents of the DATA segment
    process_section_content(obj_fp, "Disassembly of section .text:", &mem->data);

    // set the rest of the BSS segment
    mem->bss.size = mem->memory_end_addr - mem->bss.addr;
    mem->bss.bytes = calloc(mem->bss.size, 1);

    // read assembly instructions and their addresses
    read_assembly_instructions(obj_fp, assembly);


    // extract the symbols from RODATA
    get_symbol_data(obj_fp, "Disassembly of section .data:", &mem->rodata);

    // extract the symbols from DATA
    get_symbol_data(obj_fp, "Disassembly of section .bss:", &mem->data);

    // extract the symbols from BSS
    get_symbol_data(obj_fp, "random bullshit go", &mem->bss);


    pclose(obj_fp);
}
