#include <unistd.h>
#include <errno.h>
#include <sys/wait.h>
#include <string.h>

#include "preprocessor.h"
#include "serializer.h"
#include "utils.h"
#include "emu.h"


#define GCC_PATH   "/usr/bin/gcc"


struct MemoryLayout mem_layout = {0};
struct AssemblyText assembly   = {0};



void dispose_segment(struct MemorySegment *seg)
{
    free(seg->bytes);
    seg->bytes = NULL;

    for (int i = 0; i < seg->num_symbols; i++)
    {
        free(seg->symbols[i]->name);
        seg->symbols[i]->name = NULL;

        free(seg->symbols[i]->bytes);
        seg->symbols[i]->bytes = NULL;

        free(seg->symbols[i]);
        seg->symbols[i] = NULL;
    }

    free(seg->symbols);
    seg->symbols = NULL;
}

void dispose(struct MemoryLayout *mem, struct AssemblyText *assembly)
{
    free(mem->text.seg.bytes);
    mem->text.seg.bytes = NULL;

    dispose_segment(&mem->rodata);
    dispose_segment(&mem->data);
    dispose_segment(&mem->bss);


    for (int i = 0; i < assembly->num_lines; i++)
    {
        free(assembly->lines[i]);
        assembly->lines[i] = NULL;
    }

    free(assembly->lines);
    assembly->lines = NULL;
    free(assembly->addresses);
    assembly->addresses = NULL;
}


int main(int argc, char *argv[])
{
    //#define DEBUG
    #ifdef DEBUG
    argc = 2;
    #endif

    if (argc != 2)
    {
        fprintf(stderr, "Usage: %s <assembly_file>\n", argv[0]);
        exit(1);
    }

    if ( remove(COMPILED_FILE_PATH) == -1 && errno != ENOENT )
    {
        perror("Error removing compiled assembly file");
        exit(1);
    }

    #ifdef DEBUG
    system(GCC_PATH " -g ~/Desktop/assembly_files/printf_call.s -g -o " COMPILED_FILE_PATH " -no-pie");
    #else
    pid_t pid = fork();

    if (pid == -1)
    {
        perror("Fork failed");
        exit(1);
    }
    else if (pid == 0) // child
    {
        // execl will replace the currently running process with the call to GCC,
        // so no lines of code will run after execl, but only if GCC successfully runs
        execl(GCC_PATH, "gcc", argv[1], "-g", "-o", COMPILED_FILE_PATH, "-no-pie", (char *)NULL);

        // only runs if execl fails
        perror("Failed to compile the assembly file");
        exit(1);
    }
    else // parent
    {
        // wait for the child process to die
        waitpid(pid, NULL, 0);
        // successful compilation, resume normal program execution
    }
    #endif


    int insn_cnt = 0;

    // after compiling the assembly file, we disassemble it using objdump
    // and process the resulting output
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
    emulate(&mem_layout.text);
    // #######################################################

    printf("Number of instructions executed: %d\n\n", insn_cnt);

    destroy_serializer();
    dispose(&mem_layout, &assembly);


    return EXIT_SUCCESS;
}
