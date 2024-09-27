import dearpygui.dearpygui as dpg
from deserializer import *
from emu_dataclasses import *
import sys, os
from subprocess import call


program: ExecutedProgram
counter: int
lines_of_code: list[str]
rsp_row_idx = 0
stack_num_table_rows = 128
SCALE = 15
rsp_row_highlight_color = [255, 22, 22, 100]
symbol_row_color = [7, 126, 22, 255]
all_sym_row_items = []


def step(sender, app_data, user_data: int) -> None:
    global program, counter, lines_of_code, rsp_row_idx
    counter += int(user_data)

    has_program_executed = counter >= len(program.contexts) - 1

    dpg.set_value('#insn_cnt_info', counter)

    dpg.configure_item('#next', enabled=not has_program_executed)
    dpg.configure_item('#prev', enabled=(counter != 0))

    dpg.configure_item(item="#code", default_value=lines_of_code[program.contexts[counter].insn.index])


    for i, reg in enumerate(main_regs):
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
            dpg.set_value(f'#{ reg_part }_val_dec', val)


    for i, col_idx in enumerate(range(stack_num_table_rows)):
        dpg.set_value(f'#stack_row_addr{col_idx:03}', f'{program.mem_layout.stack_start_addr -8 - i:#06x}:')
        dpg.set_value(f'#stack_row_val_hex{col_idx:03}', f'{program.contexts[counter].stack.content[i]:#04x}')
        dpg.set_value(f'#stack_row_val_dec{col_idx:03}', f'{program.contexts[counter].stack.content[i]:3}')

    dpg.unhighlight_table_row('#stack', rsp_row_idx)
    rsp_row_idx = stack_num_table_rows - abs(program.contexts[counter].regs.RSP - program.mem_layout.stack_start_addr)
    dpg.highlight_table_row('#stack', rsp_row_idx, rsp_row_highlight_color)

    # update .data segment symbols
    for sym in [sym for sym in program.contexts[counter].dynamic_mem.data.symbols if sym.name not in irrelevant_symbols]:

        # dpg.set_item_label(f'#{ sym.name }_val_hex', label='0x0')
        # dpg.set_item_label(f'#{ sym.name }_val_dec', label='0')

        for i, byte in enumerate(sym.bytes):
            dpg.set_value(item=f'#{ sym.name }_val_hex_{ i }', value=f'{byte:#04x}')
            dpg.set_value(item=f'#{ sym.name }_val_dec_{ i }', value=f'{ byte }')

    # update .bss segment symbols
    for sym in [sym for sym in program.contexts[counter].dynamic_mem.bss.symbols if sym.name not in irrelevant_symbols]:

        # dpg.set_item_label(f'#{ sym.name }_val_hex', label='0x0')
        # dpg.set_item_label(f'#{ sym.name }_val_dec', label='0')

        for i, byte in enumerate(sym.bytes):
            dpg.set_value(item=f'#{ sym.name }_val_hex_{ i }', value=f'{byte:#04x}')
            dpg.set_value(item=f'#{ sym.name }_val_dec_{ i }', value=f'{ byte }')




def start_gui():

    global counter, lines_of_code
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

    # dpg.configure_app(manual_callback_management=True)


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
        global program, lines_of_code, counter, rsp_row_idx
        counter = 0

        file_path = app_data["file_path_name"]

        silencer = '' #'>/dev/null 2>&1'

        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        call(f'{ bundle_dir }/asemu { file_path }' + silencer, shell=True)

        program = des.get_executed_program()

        dpg.configure_item('#next', enabled=True)

        lines_of_code = [f'{ addr:#08x}:\t{ program.code.lines[i] }' for i, addr in enumerate(program.code.addresses)]
        dpg.configure_item(item="#code", items=lines_of_code, default_value=lines_of_code[program.contexts[counter].insn.index])


        for i, reg in enumerate(main_regs):
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
                dpg.set_value(f'#{ reg_part }_val_dec', val)


        for i, row_idx in enumerate(range(stack_num_table_rows)):
            dpg.set_value(f'#stack_row_addr{row_idx:03}', f'{program.mem_layout.stack_start_addr - 8 - i:#06x}:')
            dpg.set_value(f'#stack_row_val_hex{row_idx:03}', f'{program.contexts[counter].stack.content[i]:#04x}')
            dpg.set_value(f'#stack_row_val_dec{row_idx:03}', f'{program.contexts[counter].stack.content[i]:3}')


        dpg.unhighlight_table_row('#stack', rsp_row_idx)
        rsp_row_idx = stack_num_table_rows - abs(program.contexts[counter].regs.RSP - program.mem_layout.stack_start_addr)
        dpg.highlight_table_row('#stack', rsp_row_idx, rsp_row_highlight_color)


        # delete previous symbols so they won't be duplicated
        for row_item in all_sym_row_items:
            dpg.delete_item(row_item)

        for sym in [sym for sym in program.static_mem.rodata.symbols if sym.name not in irrelevant_symbols]:
            with dpg.table_row(parent='#rodata_syms', tag=f'#{ sym.name }_row'):

                dpg.add_selectable(label=sym.name, indent=5, span_columns=True, callback=show_symbol_parts, user_data=sym)
                # dpg.add_selectable(label='0x0', tag=f'#{ sym.name }_val_hex', indent=50)
                # dpg.add_selectable(label='0', tag=f'#{ sym.name }_val_dec', indent=70)

                all_sym_row_items.append(f'#{ sym.name }_row')

            for i, byte in enumerate(sym.bytes):
                with dpg.table_row(parent='#rodata_syms', tag=f'#{ sym.name }_hidden_{ i }', show=False):

                    all_sym_row_items.append(f'#{ sym.name }_hidden_{ i }')

                    dpg.add_text(f'{sym.addr + i:#08x}', indent=15)
                    dpg.add_text(f'{byte:#04x}', tag=f'#{ sym.name }_val_hex_{ i }', indent=30)
                    dpg.add_text(byte, tag=f'#{ sym.name }_val_dec_{ i }', indent=50)


        for sym in [sym for sym in program.contexts[counter].dynamic_mem.data.symbols if sym.name not in irrelevant_symbols]:
            with dpg.table_row(parent='#data_syms', tag=f'#{ sym.name }_row'):

                dpg.add_selectable(label=sym.name, indent=5, span_columns=True, callback=show_symbol_parts, user_data=sym)
                # dpg.add_selectable(label='0x0', tag=f'#{ sym.name }_val_hex', indent=50)
                # dpg.add_selectable(label='0', tag=f'#{ sym.name }_val_dec', indent=70)

                all_sym_row_items.append(f'#{ sym.name }_row')

            for i, byte in enumerate(sym.bytes):
                with dpg.table_row(parent='#data_syms', tag=f'#{ sym.name }_hidden_{ i }', show=False):

                    all_sym_row_items.append(f'#{ sym.name }_hidden_{ i }')

                    dpg.add_text(f'{sym.addr + i:#08x}', indent=15)
                    dpg.add_text(f'{byte:#04x}', tag=f'#{ sym.name }_val_hex_{ i }', indent=30)
                    dpg.add_text(byte, tag=f'#{ sym.name }_val_dec_{ i }', indent=50)


        for sym in [sym for sym in program.contexts[counter].dynamic_mem.bss.symbols if sym.name not in irrelevant_symbols]:
            with dpg.table_row(parent='#bss_syms', tag=f'#{ sym.name }_row'):

                dpg.add_selectable(label=sym.name, indent=5, span_columns=True, callback=show_symbol_parts, user_data=sym)
                # dpg.add_selectable(label='0x0', tag=f'#{ sym.name }_val_hex', indent=50)
                # dpg.add_selectable(label='0', tag=f'#{ sym.name }_val_dec', indent=70)

                all_sym_row_items.append(f'#{ sym.name }_row')

            for i, byte in enumerate(sym.bytes):
                with dpg.table_row(parent='#bss_syms', tag=f'#{ sym.name }_hidden_{ i }', show=False):

                    all_sym_row_items.append(f'#{ sym.name }_hidden_{ i }')

                    dpg.add_text(f'{sym.addr + i:#08x}', indent=15)
                    dpg.add_text(f'{byte:#04x}', tag=f'#{ sym.name }_val_hex_{ i }', indent=30)
                    dpg.add_text(byte, tag=f'#{ sym.name }_val_dec_{ i }', indent=50)


    def cancel_callback(sender, app_data):
        print('Cancel was clicked.')
        print("Sender: ", sender)
        print("App Data: ", app_data)

    def show_register_parts(sender, app_data, user_data):
        for reg_part in reg_subparts[user_data]:
            table_row = f'#{ reg_part }_hidden'

            if not dpg.is_item_shown(table_row):
                dpg.show_item(table_row)
            else:
                dpg.hide_item(table_row)

    def show_symbol_parts(sender, app_data, user_data: Symbol):
        for i in range(len(user_data.bytes)):
            table_row = f'#{ user_data.name }_hidden_{ i }'

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


    with dpg.file_dialog(directory_selector=False, show=False, callback=dir_open_callback, tag="#file_dialog", width=800 ,height=500):
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


        with dpg.child_window(border=False):

            with dpg.group(horizontal=True, height=800):

                # ASSEMBLY CODE WINDOW
                with dpg.child_window(width=600, no_scrollbar=True, border=True, no_scroll_with_mouse=True):

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Assembly code')
                        dpg.add_spacer(width=334)
                        dpg.add_button(label="Prev", enabled=False, callback=step, user_data=-1, tag='#prev')
                        dpg.add_button(label="Next", enabled=False, callback=step, user_data=1, tag='#next')


                    dpg.add_listbox(tag="#code", items=lines_of_code, width=-1, num_items=34, enabled=False)

                # REGISTERS WINDOW
                with dpg.child_window(width=400, no_scrollbar=True, border=True):

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Registers')
                        dpg.add_spacer(width=15)
                        dpg.add_button(label="Open all", enabled=True, callback=show_all_subregs)
                        dpg.add_button(label="Collapse all", enabled=True, callback=hide_all_subregs)

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
                            if reg in ['R15', 'RFLAGS', 'RSP']:
                                with dpg.table_row(height=40):
                                    pass

                show_register_parts(None, None, 'RFLAGS')

                # STACK WINDOW
                with dpg.child_window(width=300, no_scrollbar=True, border=True):
                    dpg.add_text(default_value='Stack')

                    with dpg.table(tag='#stack', header_row=False, no_host_extendX=True,
                                row_background=True, resizable=False, policy=dpg.mvTable_SizingFixedFit,
                                scrollY=True):

                        dpg.add_table_column(width=-1, width_fixed=True)

                        for i in range(stack_num_table_rows):
                            with dpg.table_row():
                                with dpg.group(horizontal=True, indent=5):
                                    dpg.add_text('0x000000:', tag=f'#stack_row_addr{i:03}')
                                    dpg.add_spacer(width=30)
                                    dpg.add_text('0xff', tag=f'#stack_row_val_hex{i:03}')
                                    dpg.add_spacer(width=15)
                                    dpg.add_text('255', tag=f'#stack_row_val_dec{i:03}')

                        dpg.set_y_scroll('#stack', 999999)

                # SYMBOLS WINDOW
                with dpg.child_window(width=400, no_scrollbar=True, border=True):
                    dpg.add_text(default_value='Symbols')

                    with dpg.tree_node(label=".rodata", default_open=True):

                        with dpg.table(tag='#rodata_syms', header_row=False, row_background=False,
                                       scrollX=True, borders_outerH=True):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            dpg.add_table_column()

                    with dpg.tree_node(label=".data", default_open=True):

                        with dpg.table(tag='#data_syms', header_row=False, row_background=False,
                                       scrollX=True, borders_outerH=True):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            dpg.add_table_column()

                    with dpg.tree_node(label=".bss", default_open=True):

                        with dpg.table(tag='#bss_syms', header_row=False, row_background=False,
                                        scrollX=True, borders_outerH=True):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            dpg.add_table_column()


        with dpg.group(tag='#num_insn_info_grp', height=-1, width=200, horizontal=True):
            dpg.add_text('Number of executed instructions: ')
            dpg.add_text('0', tag='#insn_cnt_info')







    # Start the Dear PyGui rendering loop
    dpg.create_viewport(title='Hohoemu', width=1750, height=900)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Set up the viewport resize callback
    dpg.set_viewport_resize_callback(viewport_resize_callback)
    # Adjust the window size on startup to fit the viewport
    update_positions()

    # while dpg.is_dearpygui_running():
    #     jobs = dpg.get_callback_queue() # retrieves and clears queue
    #     dpg.run_callbacks(jobs)
    #     dpg.render_dearpygui_frame()


    dpg.start_dearpygui()
    dpg.destroy_context()
