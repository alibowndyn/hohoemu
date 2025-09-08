#include <string.h>
#include <fcntl.h>

#include "emu.h"
#include "utils.h"
#include "serializer.h"



uc_engine *uc;
uc_hook insn_hook_handle, mem_access_handle, invalid_mem_access_handle;
uint8_t *stack_content;
extern struct MemoryLayout mem_layout;
extern struct AssemblyText assembly;


static uc_err _uc_err_check(uc_err err, const char *expr)
{
    if (err != UC_ERR_OK) {
        fprintf(stderr, "Failed on\n\t%s\nwith error: %s\n", expr, uc_strerror(err));
        exit(1);
    }
    else {
        //fprintf(stderr, "Succeeded on\n\t%s\n\n", expr);
    }

    return err;
}

#define UC_ERR_CHECK(x)     \
    _uc_err_check(x, #x)


#define ABORT()             \
{                           \
    uc_close(uc);           \
    exit(EXIT_FAILURE);     \
}

#define ADD_HOOK(hook_handle, type, callback, user_data)    \
    uc_hook_add(uc, &hook_handle, type, (void *)callback, (void *)user_data, 1, 0)



/**
 * @brief Read and save the contents of the registers listed in `x86_64_registers`
 */
static void read_registers()
{
    puts("\n\n----------NEW EXECUTION CONTEXT----------"\
         "\n\n!!!!THIS IS THE STATE OF THE PROCESSOR AFTER THE LAST EXECUTED INSTRUCTION!!!!"\
         "\n\nREGISTERS:\n");

    for (int i = 0; i < NUM_OF_REGISTERS_TO_READ; i++)
    {
        if (UC_ERR_CHECK( uc_reg_read(uc, x86_64_registers[i], &reg_contents[i]) ))
            ABORT()

        printf("    %10s:   %ld\n", x86_64_register_names[i], reg_contents[i]);
    }
}

/**
 * @brief Read and save the content of the stack
 */
static void read_stack()
{
    size_t stack_size = STACK_BYTES_TO_WRITE;
    stack_content = malloc(stack_size);

    if (UC_ERR_CHECK( uc_mem_read(uc, STACK_START_ADDR - STACK_BYTES_TO_WRITE, stack_content, stack_size) ))
        ABORT()

    printf("\nSIZE OF THE STACK: %zu bytes\nSTACK CONTENT:\n\t", stack_size);
    for (size_t i = 0; i < stack_size; i++)
    {
        printf("%02u ", stack_content[i]);
    }

    puts("");
}

static void write_symbols_from_dynamic_memory_segments()
{
    for (int i = 0; i < mem_layout.data.num_symbols; i++)
    {
        if (UC_ERR_CHECK( uc_mem_read(uc, mem_layout.data.symbols[i]->addr, mem_layout.data.symbols[i]->bytes, mem_layout.data.symbols[i]->size) ) )
            ABORT()

        write_symbol_info(mem_layout.data.symbols[i]);
    }

    for (int i = 0; i < mem_layout.bss.num_symbols; i++)
    {
        if (UC_ERR_CHECK( uc_mem_read(uc, mem_layout.bss.symbols[i]->addr, mem_layout.bss.symbols[i]->bytes, mem_layout.bss.symbols[i]->size) ) )
            ABORT()

        write_symbol_info(mem_layout.bss.symbols[i]);
    }
}

static int should_stop_emulation(uint32_t size, __uint128_t insn_bytecode)
{
    uint64_t stack_at_rsp = 0;
    if (UC_ERR_CHECK( uc_mem_read(uc, REG_RSP, &stack_at_rsp, sizeof(stack_at_rsp)) ))
        ABORT()

    printf("\nINSN'S BYTECODE: %#*llx\tSIZE OF INSN IN BYTES: %u\tRIP: %#lx\n", size, (long long)insn_bytecode, size, REG_RIP);
    printf("\nRSP: %#08lx\tSTACK AT RSP: %#08lx\n\n", REG_RSP, stack_at_rsp);


    uint8_t should_stop = (insn_bytecode == RET_INSN_BYTECODE && stack_at_rsp == STACK_CANARY);
    if (!should_stop)
        write_separator();


    return should_stop;
}

/**
 * @brief Callback function for tracing code (UC_HOOK_CODE & UC_HOOK_BLOCK)
 *
 * @param address: address where the code is being executed
 * @param size: size of machine instruction(s) being executed, or 0 when size is unknown
 * @param user_data: user data passed to tracing APIs.
 */
static void hook_insn(uc_engine *uc, uint64_t address, uint32_t size, void *user_data)
{
    // increase the counter (passed in through `user_data`) that
    // counts the number of instructions executed
    (*(uint32_t *)user_data)++;

    read_registers();
    read_stack();

    write_registers(NUM_OF_REGISTERS_TO_READ, reg_contents);
    // STACK_START_ADDR - REG_RSP
    write_stack_content(STACK_BYTES_TO_WRITE, stack_content);


    uc_mem_read(uc, mem_layout.data.addr, mem_layout.data.bytes, mem_layout.data.size);
    uc_mem_read(uc, mem_layout.bss.addr, mem_layout.bss.bytes, mem_layout.bss.size);
    write_memory_layout(&mem_layout, STACK_START_ADDR, STACK_END_ADDR, 0);


    int index = index_of_memory_address(assembly.addresses, assembly.num_lines, address);
    if ( index != -1 )
        printf("Isns at address[%#lx]: %s\n", assembly.addresses[index], assembly.lines[index]);

        // an x86-64 instruction can be up to 15 bytes in length
    __uint128_t insn_bytecode = 0;
    if (UC_ERR_CHECK( uc_mem_read(uc, address, &insn_bytecode, size) ))
        ABORT()


    write_instruction_info(index, size, insn_bytecode);

    write_symbols_from_dynamic_memory_segments();

    // if we are about to execute the last `ret` instruction, stop the emulation
    if ( should_stop_emulation(size, insn_bytecode) )
    {
        if (UC_ERR_CHECK( uc_emu_stop(uc) ))
            ABORT()
    }
}

/**
 * @brief Callback function for hooking memory (READ, WRITE & FETCH)
 *
 * @param type: this memory is being READ, or WRITE
 * @param address: address where the code is being executed
 * @param size: size of data being read or written
 * @param value: value of data being written to memory, or irrelevant if type = READ.
 * @param user_data: user data passed to tracing APIs
 */
static void hook_mem_access(uc_engine *uc, uc_mem_type type, uint64_t address, int size, uint64_t value, void *user_data)
{
    uint64_t rip;
    if (UC_ERR_CHECK( uc_reg_read(uc, UC_X86_REG_RIP, &rip) ))
        ABORT()


    switch (type)
    {
    case UC_MEM_READ:
        printf("MEMORY READ:\n"
               "Reading [%d] bytes of data at address [%#lx].\n"
               "RIP: %#lx\n", size, address, rip);
        break;

    case UC_MEM_WRITE:
        printf("MEMORY WRITE:\n"
               "Writing [%d] bytes of data with value [d:%lu  -  h:%#lx] at address [%#lx].\n"
               "RIP: %#lx\n", size, value, value, address, rip);
        break;

    case UC_MEM_FETCH:
        printf("MEMORY FETCH:\n"
               "Fetching [%d] bytes of data at address [%#lx].\n"
               "RIP: %#lx\n", size, address, rip);
        break;

    default:
        break;
    }
}

/**
 * @brief Callback function for handling invalid memory access events (UNMAPPED and PROT events)
 *
 * @param type: this memory is being READ, or WRITE
 * @param address: address where the code is being executed
 * @param size: size of data being read or written
 * @param value: value of data being written to memory, or irrelevant if type = READ.
 * @param user_data: user data passed to tracing APIs
 */
static void hook_mem_invalid(uc_engine *uc, uc_mem_type type, uint64_t address, int size, uint64_t value, void *user_data)
{
    uint64_t rip;
    if (UC_ERR_CHECK( uc_reg_read(uc, UC_X86_REG_RIP, &rip) ))
        ABORT()

    switch (type)
    {
    case UC_MEM_READ_UNMAPPED:
        printf("INVALID READ FROM UNMAPPED MEMORY:\n"
               "Tried to read [%d] bytes of data at address [%#lx].\n"
               "RIP: %#lx\n", size, address, rip);
        break;

    case UC_MEM_WRITE_UNMAPPED:
        printf("INVALID WRITE TO UNMAPPED MEMORY:\n"
               "Tried to write [%d] bytes of data with value [d:%lu  -  h:%#lx] at address [%#lx].\n"
               "RIP: %#lx\n", size, value, value, address, rip);
        break;

    case UC_MEM_FETCH_UNMAPPED:
        printf("INVALID FETCH FROM UNMAPPED MEMORY:\n"
               "Tried to fetch [%d] bytes of data at address [%#lx].\n"
               "RIP: %#lx\n", size, address, rip);
        break;

    case UC_MEM_READ_PROT:
        printf("INVALID READ FROM READ-PROTECTED MEMORY:\n"
               "Tried to read [%d] bytes of data at address [%#lx].\n"
               "RIP: %#lx\n", size, address, rip);
        break;

    case UC_MEM_WRITE_PROT:
        printf("INVALID WRITE TO WRITE-PROTECTED MEMORY:\n"
               "Tried to write [%d] bytes of data with value [d:%lu  -  h:%#lx] at address [%#lx].\n"
               "RIP: %#lx\n", size, value, value, address, rip);
        break;

    case UC_MEM_FETCH_PROT:
        printf("INVALID FETCH FROM READ-PROTECTED MEMORY:\n"
               "Tried to fetch [%d] bytes of data at address [%#lx].\n"
               "RIP: %#lx\n", size, address, rip);
        break;

    default:
        break;
    }
}



static void init_virtual_mem(struct MemoryLayout *mem)
{
    printf("\n--------- ALLOCATING VIRTUAL MEMORY FOR TEXT, RODATA, DATA and BSS segments ---------\n");
    printf("STARTING ADDRESSES:\nTEXT:   %#lx\nRODATA: %#lx\nDATA:   %#lx\nBSS:    %#lx\n\n",
            mem->text.seg.addr, mem->rodata.addr, mem->data.addr, mem->bss.addr);


    // the `& 0xfffff000` part rounds up the address to the next biggest number divisible by 4096 (4kB)
    uint64_t mem_size_to_map = ((mem->memory_end_addr - CODE_START_ADDR) + (UC_MEM_ALIGN_SIZE - 1)) & 0xfffff000;

    // allocate memory for the TEXT, RODATA, DATA and BSS segments
    if (UC_ERR_CHECK( uc_mem_map(uc, CODE_START_ADDR, mem_size_to_map, UC_PROT_ALL) ))
        ABORT()


    // load the TEXT segment's content in memory
    if (UC_ERR_CHECK( uc_mem_write(uc, mem->text.seg.addr, mem->text.seg.bytes, mem->text.seg.size) ))
        ABORT()

    // load the RODATA segment's content in memory
    if (mem->rodata.size != 0)
    {
        if (UC_ERR_CHECK( uc_mem_write(uc, mem->rodata.addr, mem->rodata.bytes, mem->rodata.size) ))
            ABORT()
    }

    // load the DATA segment's content in memory
    if (mem->data.size != 0)
    {
        if (UC_ERR_CHECK( uc_mem_write(uc, mem->data.addr, mem->data.bytes, mem->data.size) ))
            ABORT()
    }


    // allocate memory for the stack
    if (UC_ERR_CHECK( uc_mem_map(uc, STACK_END_ADDR, STACK_SIZE, UC_PROT_ALL) ))
        ABORT()


    // read random bytes from `/dev/urandom`, which contains random data generated by a PRNG
    uint8_t *random_bytes = malloc(STACK_SIZE);
    int fd = open("/dev/urandom", O_RDONLY);
    read(fd, random_bytes, STACK_SIZE);

    // fill the stack with random bytes, simulating the stack as having junk data
    if (UC_ERR_CHECK( uc_mem_write(uc, STACK_END_ADDR, random_bytes, STACK_SIZE) ))
        ABORT()


    // Set a guard value at the start of the stack. This value will be checked before the execution
    // of every `ret` instruction.
    // This guard value is supposed to represent the return address that the "OS pushed" on to the
    // stack by a call instruction when it "called" our program (the bytecode that the emu executes).
    uint64_t stack_canary = STACK_CANARY;
    if (UC_ERR_CHECK( uc_mem_write(uc, STACK_CANARY_ADDR, &stack_canary, sizeof(stack_canary)) ))
        ABORT()


    close(fd);
    free(random_bytes);
}

static void init_hooks(int *instruction_count)
{
    if (UC_ERR_CHECK( ADD_HOOK(insn_hook_handle,          UC_HOOK_CODE,         hook_insn, instruction_count) ))
        ABORT()

    if (UC_ERR_CHECK( ADD_HOOK(mem_access_handle,         UC_HOOK_MEM_VALID,    hook_mem_access, NULL) ))
        ABORT()

    if (UC_ERR_CHECK( ADD_HOOK(invalid_mem_access_handle, UC_HOOK_MEM_UNMAPPED, hook_mem_invalid, NULL) ))
        ABORT()
    if (UC_ERR_CHECK( ADD_HOOK(invalid_mem_access_handle, UC_HOOK_MEM_PROT,     hook_mem_invalid, NULL) ))
        ABORT()
}

static void init_regs()
{
    uint64_t rsp = STACK_CANARY_ADDR;

    if (UC_ERR_CHECK( uc_reg_write(uc, UC_X86_REG_RSP, &rsp) ))
        ABORT()

    if (UC_ERR_CHECK( uc_reg_write(uc, UC_X86_REG_RBP, &rsp) ))
        ABORT()
}



void init_emu(struct MemoryLayout *memory_layout, int *instruction_count)
{
    // create a new instance of unicorn engine with x86 architecture in 64-bit mode.
    if (UC_ERR_CHECK( uc_open(UC_ARCH_X86, UC_MODE_64, &uc) ))
        ABORT()

    init_virtual_mem(memory_layout);
    init_hooks(instruction_count);
    init_regs(memory_layout->text.seg.addr);
}


int emulate(struct TextSegment *text_segment)
{
    // emulate code in infinite time, unlimited number of instructions
    if (UC_ERR_CHECK( uc_emu_start(uc, text_segment->main_addr, text_segment->seg.addr + text_segment->seg.size, 0, 0) ))
        ABORT()



    /////////////////////////////////////////////////////////////////////
    /////         EMULATION DONE || RETRIEVE AX AND CLEAN UP
    /////////////////////////////////////////////////////////////////////
    puts("\n\n-----------------------------------------------------\n"
             "               ### EMULATION DONE ###\n"
             "-----------------------------------------------------");


    printf("Contents of AL register:\n  "            \
           "hex: %#x   dec: %u\n\n", (uint8_t)REG_RAX, (uint8_t)REG_RAX);


    uc_hook_del(uc, insn_hook_handle);
    uc_hook_del(uc, mem_access_handle);
    uc_close(uc);


    return EXIT_SUCCESS;
}
