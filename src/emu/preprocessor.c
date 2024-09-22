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
        // When the two buffers contains lines like these:
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

    pclose(obj_fp);
}
