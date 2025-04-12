CC          := /usr/bin/gcc
SRCS        := $(wildcard src/emu/*.c)
HEADERS     := $(wildcard src/emu/*.h)
EMU         := asemu
TARGET      := src/app.py
OUT_DIR     := build
ASSETS_DIR  := assets
SPEC_DIR    := $(OUT_DIR)/spec
DIST_DIR    := $(OUT_DIR)/dist
BUILD_DIR   := $(OUT_DIR)/build

COMPILED_FILE_PATH     := /tmp/compiled_assembly_file
SERIALIZED_OUTPUT_PATH := /tmp/emu_output_240830.txt


.PHONY: all out install clean
all: install


out: $(SRCS)
	$(CC) -Wall -Wextra $(SRCS) -L lib -lunicorn -lm -o $(EMU)


install: clean out
	mkdir -p $(SPEC_DIR)
	cp $(EMU) $(SPEC_DIR)
	cp -r $(ASSETS_DIR) $(SPEC_DIR)

	pyinstaller \
		--specpath $(SPEC_DIR) \
		--distpath $(DIST_DIR) \
		--workpath $(BUILD_DIR) \
		--add-data="$(ASSETS_DIR)/Consolas.ttf:$(ASSETS_DIR)" \
		--add-data="$(EMU):." \
		--name hohoemu \
		$(TARGET) \
		--onefile
	xdg-open $(DIST_DIR) &



#########################################################################################

# run the compiled assembly file and print out the return value
# same as 'echo $?', basically printing out the contents of AX
echo: $(COMPILED_FILE_PATH)
	$(COMPILED_FILE_PATH) 2>1


memcheck:
	valgrind --leak-check=full --track-origins=yes ./$(TARGET)


text: $(COMPILED_FILE_PATH)
	objdump -sSt --source-comment --no-show-raw-insn --section=.text -M "x86-64,intel" $(COMPILED_FILE_PATH)

bss: $(COMPILED_FILE_PATH)
	objdump -sSt --source-comment --no-show-raw-insn --section=.bss $(COMPILED_FILE_PATH)

rodata: $(COMPILED_FILE_PATH)
	objdump -sSt --source-comment --no-show-raw-insn --section=.rodata $(COMPILED_FILE_PATH)

data: $(COMPILED_FILE_PATH)
	objdump -sSt --source-comment --no-show-raw-insn --section=.data $(COMPILED_FILE_PATH)


print_bridge:
	/usr/bin/cat $(SERIALIZED_OUTPUT_PATH)

#########################################################################################



clean:
	rm -rf $(OUT_DIR) $(EMU)
