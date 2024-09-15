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



.PHONY: all out install clean
all: install


out: $(SRCS)
	$(CC) -Wall -Wextra -O3 $(SRCS) -L lib -lunicorn -lm -o $(EMU)


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


clean:
	rm -rf $(OUT_DIR) $(EMU)
