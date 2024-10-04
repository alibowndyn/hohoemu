import dearpygui.dearpygui as dpg
from deserializer import *
from emu_dataclasses import *
import sys, os
from subprocess import call


program: ExecutedProgram = None
counter: int
lines_of_code: list[str]
rsp_row_idx = 0
stack_num_table_rows = 128
SCALE = 15
highlighted_row_idx = 0
rsp_row_highlight_color = [255, 22, 22, 200]
code_row_highlight_color = [255, 22, 22, 200]
symbol_row_color = [7, 126, 22, 255]
items_to_delete_before_setup = []
is_table_created = False

seg_to_show = {'rodata': [], 'data': [], 'bss': []}
mem_addr_txts = []
themes = []
row_height = 25
direction = 0

breakpoints = []
curr_breakpoint = ''
program_ended = False




def build_symbol_table_for_segment(seg: MemorySegment):
    l = [sym for sym in seg.symbols if sym.name not in irrelevant_symbols]
    j = 0
    for j, (sym, row) in enumerate(zip(l, seg_to_show[seg.name])):
        dpg.show_item(item=f'{ seg.name }_{ j }_sel')
        dpg.set_item_label(item=f'{ seg.name }_{ j }_sel', label=sym.name)
        dpg.set_item_user_data(item=f'{ seg.name }_{ j }_sel', user_data=(seg.name, j, sym))

        for i, byte in enumerate(sym.bytes):
            dpg.set_value(item=f'#{ seg.name }_{ j }_addr_{ i }', value=f'{sym.addr + i:#08x}')
            dpg.set_value(item=f'#{ seg.name }_{ j }_val_hex_{ i }', value=f'{byte:#04x}')
            dpg.set_value(item=f'#{ seg.name }_{ j }_val_dec_{ i }', value=f'{byte}  ')

    # for row in seg_to_show[seg.name][j:]:
    #     dpg.hide_item(row)
    #     dpg.set_item_height(item=row, height=0)


def build_code_table():
    global program, counter, lines_of_code, is_table_created

    for i, (addr, line) in enumerate(lines_of_code):
        dpg.show_item(item=f'#code_row_{ i }')
        dpg.set_item_label(item=f'#code_addr_{ i }', label=f'{addr:#08x}:')
        dpg.set_value(item=f'#code_line_{ i }', value=f'{line}  ')
    for i in range(program.code.num_lines, 128):
        dpg.hide_item(item=f'#code_row_{ i }')

    update_code()
    # is_table_created = True

def update_code_window_scroll_position(row_idx: int):
    # only do the calculations if the the row is not visible
    if dpg.is_item_visible(f'#code_addr_{ highlighted_row_idx }'):
        return

    row_y = highlighted_row_idx * row_height

    # if row_y is closer to the top of the code window, scroll to the top, else scroll to the bottom
    if row_y < 800 - row_y:
        scroll_height = 0
    else:
        scroll_height = row_height * program.contexts[len(program.contexts) - 1].insn.index

    dpg.set_y_scroll('#code', scroll_height)


def update_code():
    global program, counter, lines_of_code, highlighted_row_idx, direction, row_height, breakpoints, curr_breakpoint, themes

    dpg.unhighlight_table_row(table='#code', row=highlighted_row_idx)

    # color the previously highlighted row's address text back to address theme
    dpg.bind_item_theme(f'#code_addr_{ highlighted_row_idx }', theme=themes[0])

    highlighted_row_idx = program.contexts[counter].insn.index
    dpg.highlight_table_row(table='#code', row=highlighted_row_idx, color=code_row_highlight_color)

    # color the highlighted row's address text to white so it can be seen better
    dpg.bind_item_theme(f'#code_addr_{ highlighted_row_idx }', theme=themes[1])

    for bp in breakpoints:
        dpg.bind_item_theme(bp[0], theme=themes[2])

    update_code_window_scroll_position(highlighted_row_idx)


def update_registers():
    global program, counter

    for reg in main_regs:
        val = program.contexts[counter].regs.rdict[reg]

        dpg.set_item_label(f'#{ reg }_val_hex', f'{val:#x}')
        dpg.set_item_label(f'#{ reg }_val_dec', val)

        for j in range(len(reg_subparts[reg])):
            reg_part = reg_subparts[reg][j]

            if reg_part in flags:
                val = extract_rflag_bits(program.contexts[counter].regs.rdict['RFLAGS'], reg_part)
            else:
                val = program.contexts[counter].regs.rdict[reg_part]

            dpg.set_value(f'#{ reg_part }_val_hex', f'{val:#x}')
            dpg.set_value(f'#{ reg_part }_val_dec', f'{val}  ')


def update_stack():
    global program, counter, rsp_row_idx, themes

    for i, row_idx in enumerate(range(stack_num_table_rows)):
        dpg.set_value(f'#stack_row_addr{row_idx:03}', f'{program.mem_layout.stack_start_addr - 128 + i:#06x}:')
        dpg.set_value(f'#stack_row_val_hex{row_idx:03}', f'{program.contexts[counter].stack.content[i]:#04x}')
        dpg.set_value(f'#stack_row_val_dec{row_idx:03}', f'{program.contexts[counter].stack.content[i]:3}  ')

    dpg.unhighlight_table_row('#stack', rsp_row_idx)
    dpg.bind_item_theme(f'#stack_row_addr{rsp_row_idx:03}', theme=themes[1])
    rsp_row_idx = stack_num_table_rows - abs(program.contexts[counter].regs.RSP - program.mem_layout.stack_start_addr)
    dpg.highlight_table_row('#stack', rsp_row_idx, rsp_row_highlight_color)
    dpg.bind_item_theme(f'#stack_row_addr{rsp_row_idx:03}', theme=themes[1])


def update_symbols_for_segment(seg: MemorySegment):
    global program, counter

    for j, sym in enumerate([sym for sym in seg.symbols if sym.name not in irrelevant_symbols]):
        for i, byte in enumerate(sym.bytes):
            dpg.set_value(item=f'#{ seg.name }_{ j }_val_hex_{ i }', value=f'{byte:#04x}')
            dpg.set_value(item=f'#{ seg.name }_{ j }_val_dec_{ i }', value=f'{ byte }  ')


def step(sender, app_data, user_data: int) -> None:
    global program, counter, lines_of_code, rsp_row_idx, direction, program_ended

    program_ended = False
    direction = int(user_data)
    tmp_counter = counter + direction

    if (program is None) or (tmp_counter >= len(program.contexts)):
        program_ended = True
        return
    elif tmp_counter == -1:
        return

    counter = tmp_counter
    dpg.set_value('#insn_cnt_info', counter)

    update_code()
    update_registers()
    update_stack()

    update_symbols_for_segment(program.contexts[counter].dynamic_mem.data)
    update_symbols_for_segment(program.contexts[counter].dynamic_mem.bss)


def handle_mouse_wheel_scroll(sender, app_data):
    return
    if dpg.is_mouse_button_down(dpg.mvMouseButton_Right):
        step(None, None, -1 if app_data > 0 else 1)

def show_register_parts(sender, app_data, user_data):
    for reg_part in reg_subparts[user_data]:
        table_row = f'#{ reg_part }_hidden'

        if not dpg.is_item_shown(table_row):
            dpg.show_item(table_row)
        else:
            dpg.hide_item(table_row)

def show_symbol_parts(_, __, user_data: tuple[str, int, Symbol]):
    for i in range(len(user_data[2].bytes)):
        table_row = f'#{ user_data[0] }_{ user_data[1] }_hidden_{ i }'

        if not dpg.is_item_shown(table_row):
            dpg.show_item(table_row)
        else:
            dpg.hide_item(table_row)

def show_all_subregs():
    for reg in main_regs:
        for reg_part in reg_subparts[reg]:
            dpg.show_item(f'#{ reg_part }_hidden')

def hide_all_subregs():
    for reg in main_regs:
        for reg_part in reg_subparts[reg]:
            dpg.hide_item(f'#{ reg_part }_hidden')

def set_breakpoint(_, __, user_data):
    global breakpoints, highlighted_row_idx, themes

    dpg.bind_item_theme(item=user_data, theme=themes[2])

    addr = int(dpg.get_item_label(user_data)[:-1], 16)
    bp = (user_data, addr)

    if bp in breakpoints:
        breakpoints.remove(bp)
        is_highlighted_row = user_data == f'#code_addr_{ highlighted_row_idx }'
        dpg.bind_item_theme(item=user_data, theme=themes[1 if is_highlighted_row else 0])
    else:
        breakpoints.append(bp)

    sorted(breakpoints, key=lambda x: x[1])
    print([hex(bp[1]) for bp in breakpoints])

def continue_until_breakpoint():
    global program, counter, highlighted_row_idx, curr_breakpoint, program_ended, breakpoints

    if not breakpoints or program_ended:
        return

    bps = [bp[1] for bp in breakpoints]
    bps_tmp = bps.copy() #important
    addr = program.code.addresses[highlighted_row_idx]
    if addr in bps:
        bps_tmp.remove(addr) #important
    print([hex(bp) for bp in bps], [hex(bp) for bp in bps_tmp], hex(addr))
    reached = False
    while not reached and not program_ended:
        if a := program.code.addresses[highlighted_row_idx] not in bps_tmp:
            step(None, None, 1)
            bps_tmp = [bp[1] for bp in breakpoints] #important
        else:
            reached = True
            curr_breakpoint = [bp[0] for bp in breakpoints if bp[1] == a]

def start_gui():
    global counter, lines_of_code, row_height, mem_addr_txts
    lines_of_code = []
    counter = 0

    des = Deserializer()

    def update_positions():
        # Get the current viewport size
        vp_width = dpg.get_viewport_client_width()
        vp_height = dpg.get_viewport_client_height()

        # Adjust the main window size to match the viewport size
        dpg.set_item_width("#main_window", vp_width)
        dpg.set_item_height("#main_window", vp_height)

        dpg.set_item_pos('#num_insn_info_grp', pos=[10, vp_height - 30])

    # Callback to handle viewport resize event
    def viewport_resize_callback(sender, app_data):
        update_positions()


    # Start the Dear PyGui context
    dpg.create_context()

    with dpg.font_registry():
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        default_font = dpg.add_font(f'{ bundle_dir }/assets/Consolas.ttf', 18*2)


    def show_file_dialog():
        dpg.show_item("#file_dialog")


    def dir_open_callback(sender, app_data):
        global program, lines_of_code, counter, rsp_row_idx, is_table_created, breakpoints, program_ended, themes
        counter = 0
        program_ended = False

        for bp in breakpoints:
            dpg.bind_item_theme(bp[0], theme=themes[3])
        breakpoints = []

        file_path = app_data["file_path_name"]


        raw_assembly = open(file_path, 'r').read()
        dpg.set_value(item='#raw_assembly', value=raw_assembly)

        as_lines = raw_assembly.split('\n')


        silencer = ' > /dev/null'

        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # compile the selected assembly file
        call(f'{ bundle_dir }/asemu { file_path }' + silencer, shell=True)


        if is_table_created:
            for i in range(program.code.num_lines):
                dpg.set_value(item=f'#code_addr_{ i }', value='')
                dpg.set_value(item=f'#code_line_{ i }', value='')

            for i in range(program.code.num_lines, 128):
                dpg.hide_item(item=f'#code_row_{ i }')


        # process the file output by the emulator
        program = des.get_executed_program()

        dpg.set_value('#insn_cnt_info', 0)

        lines_of_code = [(addr, program.code.lines[i]) for i, addr in enumerate(program.code.addresses)]



        # delete some previously created items so they won't be duplicated
        for item in items_to_delete_before_setup:
            dpg.hide_item(item)


        build_code_table()
        update_code()
        update_registers()
        update_stack()

        build_symbol_table_for_segment(program.static_mem.rodata)
        build_symbol_table_for_segment(program.contexts[counter].dynamic_mem.data)
        build_symbol_table_for_segment(program.contexts[counter].dynamic_mem.bss)


    with dpg.file_dialog(directory_selector=False, show=False, callback=dir_open_callback, tag="#file_dialog", width=800, height=500):
        dpg.add_file_extension(".s", color=(0, 255, 0, 255), custom_text="[Assembly]")
        dpg.add_file_extension("", color=(150, 255, 150, 255))
        dpg.add_file_extension(".*")


    # Main Window
    with dpg.window(label="Main Program", tag='#main_window',
                    no_title_bar=True, no_move=True, no_collapse=True, no_scrollbar=True,
                    no_scroll_with_mouse=True, no_close=True, no_resize=True, pos=[0, 0]):
        dpg.bind_font(default_font)
        dpg.set_global_font_scale(0.5)

        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Load assembly file", callback=show_file_dialog)


        with dpg.group(horizontal=True, height=800):

            # ASSEMBLY CODE WINDOW
            with dpg.child_window(tag='#code_window', width=600, no_scrollbar=True, border=True, no_scroll_with_mouse=True, resizable_x=True, resizable_y=True):

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value='Assembly code')
                    dpg.add_spacer(width=15)
                    dpg.add_button(label="Previous", callback=step, user_data=-1, tag='#prev')
                    dpg.add_button(label="Next", callback=step, user_data=1, tag='#next')
                    dpg.add_button(label="Continue", callback=continue_until_breakpoint, user_data=1, tag='#cont')

                dpg.add_separator()

                with dpg.tab_bar():
                    with dpg.tab(label='Assembled code'):

                        with dpg.table(tag='#code', header_row=False, row_background=False,
                                        scrollX=True, resizable=False, policy=dpg.mvTable_SizingFixedFit):

                            dpg.add_table_column()
                            dpg.add_table_column()

                            for i in range(128):
                                with dpg.table_row(tag=f'#code_row_{ i }', height=row_height):

                                    txt = dpg.add_selectable(tag=f'#code_addr_{ i }', callback=set_breakpoint, user_data=f'#code_addr_{ i }')
                                    mem_addr_txts.append(txt)
                                    dpg.add_text(tag=f'#code_line_{ i }')

                    with dpg.tab(label='Raw code'):
                        with dpg.child_window(border=False):
                            dpg.add_text(tag='#raw_assembly')


            # REGISTERS WINDOW
            with dpg.child_window(width=400, no_scrollbar=True, border=True, resizable_x=True, resizable_y=True):

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value='Registers')
                    dpg.add_spacer(width=15)
                    dpg.add_button(label="Open all", enabled=True, callback=show_all_subregs)
                    dpg.add_button(label="Collapse all", enabled=True, callback=hide_all_subregs)

                dpg.add_separator()
                with dpg.table(tag='#regs', header_row=False, row_background=False,
                                policy=dpg.mvTable_SizingFixedFit, scrollX=True):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()

                    for i, reg in enumerate(main_regs):
                        with dpg.table_row():

                            dpg.add_selectable(label=reg, indent=5, span_columns=True, callback=show_register_parts, user_data=reg)
                            dpg.add_selectable(label='0x00', tag=f'#{ reg }_val_hex', indent=50)
                            dpg.add_selectable(label='0', tag=f'#{ reg }_val_dec', indent=70)

                        for j, subreg in enumerate(reg_subparts[reg]):
                            with dpg.table_row(tag=f'#{ subreg }_hidden', show=False):

                                reg_part = reg_subparts[reg][j]

                                dpg.add_text(reg_part, indent=15)
                                dpg.add_text('0x00', tag=f'#{ reg_part }_val_hex', indent=50)
                                dpg.add_text('0', tag=f'#{ reg_part }_val_dec', indent=70)

                        with dpg.table_row(height=5):
                            pass
                        if reg in ['R15', 'RIP', 'RFLAGS']:
                            with dpg.table_row(height=40):
                                pass

                show_register_parts(None, None, 'RFLAGS')

            # STACK WINDOW
            with dpg.child_window(width=300, no_scrollbar=True, border=True, resizable_x=True, resizable_y=True):
                dpg.add_text(default_value='Stack')

                dpg.add_separator()
                with dpg.table(tag='#stack', header_row=False, no_host_extendX=True,
                            row_background=True, resizable=False, policy=dpg.mvTable_SizingFixedFit,
                            scrollY=True):

                    dpg.add_table_column(width=-1, width_fixed=True)

                    for i in range(stack_num_table_rows):
                        with dpg.table_row():
                            with dpg.group(horizontal=True, indent=5):
                                txt = dpg.add_text('0x000000:', tag=f'#stack_row_addr{i:03}')
                                mem_addr_txts.append(txt)
                                dpg.add_spacer(width=30)
                                dpg.add_text('0xff', tag=f'#stack_row_val_hex{i:03}')
                                dpg.add_spacer(width=15)
                                dpg.add_text('255', tag=f'#stack_row_val_dec{i:03}')

                    dpg.set_y_scroll('#stack', 999999)

            # SYMBOLS WINDOW
            with dpg.child_window(width=400, border=True, resizable_x=True, resizable_y=True):
                dpg.add_text(default_value='Static data symbols')

                dpg.add_separator()

                with dpg.collapsing_header(label=".rodata", default_open=True):

                    for j in range(12):
                        sel = dpg.add_selectable(tag=f'rodata_{ j }_sel', indent=5, span_columns=True, callback=show_symbol_parts, show=False)
                        seg_to_show['rodata'].append(sel)

                        items_to_delete_before_setup.append(sel)

                        for i in range(24):
                            with dpg.group(tag=f'#rodata_{ j }_hidden_{ i }', horizontal=True, show=False, horizontal_spacing=80) as grp:

                                txt = dpg.add_text('', tag=f'#rodata_{ j }_addr_{ i }', indent=20)
                                mem_addr_txts.append(txt)
                                dpg.add_text('', tag=f'#rodata_{ j }_val_hex_{ i }')
                                dpg.add_text('', tag=f'#rodata_{ j }_val_dec_{ i }')

                                items_to_delete_before_setup.append(grp)

                with dpg.collapsing_header(label=".data", default_open=True):

                    for j in range(12):
                        sel = dpg.add_selectable(tag=f'data_{ j }_sel', indent=5, span_columns=True, callback=show_symbol_parts, show=False)
                        seg_to_show['data'].append(sel)

                        items_to_delete_before_setup.append(sel)

                        for i in range(24):
                            with dpg.group(tag=f'#data_{ j }_hidden_{ i }', horizontal=True, show=False, horizontal_spacing=80) as grp:

                                txt = dpg.add_text('', tag=f'#data_{ j }_addr_{ i }', indent=20)
                                mem_addr_txts.append(txt)
                                dpg.add_text('', tag=f'#data_{ j }_val_hex_{ i }')
                                dpg.add_text('', tag=f'#data_{ j }_val_dec_{ i }')

                                items_to_delete_before_setup.append(grp)


                with dpg.collapsing_header(label=".bss", default_open=True):

                    for j in range(12):
                        sel = dpg.add_selectable(tag=f'bss_{ j }_sel', indent=5, span_columns=True, callback=show_symbol_parts, show=False)
                        seg_to_show['bss'].append(sel)

                        items_to_delete_before_setup.append(sel)

                        for i in range(24):
                            with dpg.group(tag=f'#bss_{ j }_hidden_{ i }', horizontal=True, show=False, horizontal_spacing=80) as grp:

                                txt = dpg.add_text('', tag=f'#bss_{ j }_addr_{ i }', indent=20)
                                mem_addr_txts.append(txt)
                                dpg.add_text('', tag=f'#bss_{ j }_val_hex_{ i }')
                                dpg.add_text('', tag=f'#bss_{ j }_val_dec_{ i }')

                                items_to_delete_before_setup.append(grp)


        with dpg.group(tag='#num_insn_info_grp', height=-1, width=200, horizontal=True):
            dpg.add_text('Number of executed instructions: ')
            dpg.add_text('0', tag='#insn_cnt_info')


    # Create a theme for the main window
    with dpg.theme() as main_window_theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (33, 33, 140, 180), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (33, 33, 140, 100), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)

        with dpg.theme_component(dpg.mvSelectable):
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            # this will make sure that clicking a selectable won't change its color
            dpg.add_theme_color(dpg.mvThemeCol_Header, (37, 37, 38, -255), category=dpg.mvThemeCat_Core)

        with dpg.theme_component(dpg.mvCollapsingHeader):
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)

        with dpg.theme_component(dpg.mvTab):
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            # this will make sure that clicking a selectable won't change its color
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (37, 37, 38, -255), category=dpg.mvThemeCat_Core)

    # Create a theme for the code window
    with dpg.theme() as code_window_theme:
        with dpg.theme_component(dpg.mvTableRow):
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (37, 37, 38, 255), category=dpg.mvThemeCat_Core)

    # Create a theme for the texts showing memory addresses
    with dpg.theme() as addr_sel_theme:
        with dpg.theme_component(dpg.mvSelectable):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 150, 22, 255), category=dpg.mvThemeCat_Core)

    with dpg.theme() as break_point:
        with dpg.theme_component(dpg.mvSelectable):
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (255, 22, 22, 200), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (255, 22, 22, 200), category=dpg.mvThemeCat_Core)
            # this will make sure that clicking a selectable won't change its color
            dpg.add_theme_color(dpg.mvThemeCol_Header, (255, 22, 22, 200), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)

    with dpg.theme() as default_selectable:
        with dpg.theme_component(dpg.mvSelectable):
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (33, 33, 140, 255), category=dpg.mvThemeCat_Core)
            # this will make sure that clicking a selectable won't change its color
            dpg.add_theme_color(dpg.mvThemeCol_Header, (37, 37, 38, -255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 150, 22, 255), category=dpg.mvThemeCat_Core)

    # with dpg.theme() as addr_txt_theme:
    #     with dpg.theme_component(dpg.mvText):
    #         dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 150, 22, 255), category=dpg.mvThemeCat_Core)

    with dpg.theme() as white_text:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255), category=dpg.mvThemeCat_Core)


    themes.append(addr_sel_theme)
    themes.append(white_text)
    themes.append(break_point)
    themes.append(default_selectable)
    # themes.append(addr_txt_theme)


    with dpg.handler_registry():
        dpg.add_key_press_handler(dpg.mvKey_Down, callback=step, user_data=1)
        dpg.add_key_press_handler(dpg.mvKey_Up, callback=step, user_data=-1)
        dpg.add_key_press_handler(dpg.mvKey_Right, callback=continue_until_breakpoint)
        dpg.add_mouse_wheel_handler(callback=handle_mouse_wheel_scroll)


    dpg.bind_item_theme('#main_window', main_window_theme)
    dpg.bind_item_theme('#code_window', code_window_theme)

    # for txt in mem_addr_txts:
    #     print(txt)
    #     dpg.bind_item_theme(txt, addr_txt_theme)


    # Start the Dear PyGui rendering loop
    dpg.create_viewport(title='Hohoemu', width=1750, height=900)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Set up the viewport resize callback
    dpg.set_viewport_resize_callback(viewport_resize_callback)
    # Adjust the window size on startup to fit the viewport
    update_positions()

    dpg.start_dearpygui()
    dpg.destroy_context()
