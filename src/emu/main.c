#include <string.h>

#include "preprocessor.h"
#include "emu.h"
#include "utils.h"
#include "serializer.h"


#define MAX_COMMAND_LEN     256


struct MemoryLayout mem_layout = {0};
struct AssemblyText assembly   = {0};



void dispose(struct MemoryLayout *mem, struct AssemblyText *assembly)
{
    free(mem->text.seg.bytes);
    free(mem->rodata.bytes);
    free(mem->data.bytes);
    free(mem->bss.bytes);

    for (int i = 0; i < assembly->num_lines; i++)
    {
        // free(assembly->lines[i]);
        assembly->lines[i] = NULL;
    }

    free(assembly->lines);
    assembly->lines = NULL;
    free(assembly->addresses);
    assembly->addresses = NULL;
}


int main(int argc, char *argv[])
{
    char cmd[MAX_COMMAND_LEN] = "/usr/bin/gcc ";
    int insn_cnt = 0;

    system("/usr/bin/rm -f /tmp/compiled_assembly_file /tmp/emu_output_240830.txt");

    //#define DEBUG
    #ifdef DEBUG
                        /// THIS IS FOR DEBUGGING ///
        char *assembly_src = " ~/Desktop/assembly_files/stack_overflow.s";
    #else
        char *assembly_src = argv[argc - 1];
    #endif

    // TODO: `-g` switch should only be added when trying to compile from an assembly source file
    char *switches_src = " -g -o /tmp/compiled_assembly_file -no-pie";

    // append the source file to the command string
    strncat(cmd + strlen(cmd), assembly_src, MAX_COMMAND_LEN-1);
    // append the switches to the command string
    strncat(cmd + strlen(cmd), switches_src, MAX_COMMAND_LEN-1);


    // Compile the assembly file.
    int ret_value = system(cmd);
    if ( ret_value == -1 || ret_value != 0 ) // GCC Error
    {
        fprintf(stderr, "\nERROR: failed to compile assembly file\n\n");
        exit(1); // TODO: think of different exit codes and write it in the docs
    }

    // After compiling the assembly file, we need to call objdump
    // on it and process its output.
    process_objdump_output(&mem_layout, &assembly);


    initialize_serializer();
    write_assembly_instructions_and_addresses(&assembly);
    write_memory_layout(&mem_layout, STACK_START_ADDR, STACK_END_ADDR, 1);


    printf("\n\n.TEXT:\n\tBYTE-COUNT: %ld\n\t%#lx: ", mem_layout.text.seg.size, mem_layout.text.seg.addr);
    for (size_t i = 0; i < mem_layout.text.seg.size; i++)
        printf("%02x ", mem_layout.text.seg.bytes[i]);
    puts("");

    printf("\n\n.RODATA:\n\tBYTE-COUNT: %ld\n\t%#lx: ", mem_layout.rodata.size, mem_layout.rodata.addr);
    for (size_t i = 0; i < mem_layout.rodata.size; i++)
        printf("%02x ", mem_layout.rodata.bytes[i]);
    puts("");

    printf("\n\n.DATA:\n\tBYTE-COUNT: %ld\n\t%#lx: ", mem_layout.data.size, mem_layout.data.addr);
    for (size_t i = 0; i < mem_layout.data.size; i++)
        printf("%02x ", mem_layout.data.bytes[i]);
    puts("");

    printf("\n\n.BSS:\n\tBYTE-COUNT: %ld\n\t%#lx: ", mem_layout.bss.size, mem_layout.bss.addr);
    for (size_t i = 0; i < mem_layout.bss.size; i++)
        printf("%02x ", mem_layout.bss.bytes[i]);
    puts("");


    // ##############  WHERE THE MAGIC HAPPENS  ##############
    init_emu(&mem_layout, &insn_cnt);
    print_mapped_memory_regions();
    emulate(&mem_layout.text);
    // #######################################################


    printf("Number of instructions executed: %d\n\n", insn_cnt);


    destroy_serializer();
    dispose(&mem_layout, &assembly);

    return EXIT_SUCCESS;
}
