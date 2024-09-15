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


def step(sender, app_data, user_data: int) -> None:
    global program, counter, lines_of_code, rsp_row_idx
    counter += int(user_data)

    has_program_executed = counter >= len(program.contexts) - 1

    dpg.set_value('#insn_cnt_info', counter)

    dpg.configure_item('#next', enabled=not has_program_executed)
    dpg.configure_item('#prev', enabled=(counter != 0))

    dpg.configure_item(item="#code", default_value=lines_of_code[program.contexts[counter].insn.index])


    reg_names = list(Registers.__dataclass_fields__.keys())[:-1]
    for i, key in enumerate(reg_names):
        dpg.set_value(f'#reg_val_col{i:02}', program.contexts[counter].regs.rdict[key])


    for i, col_idx in enumerate(range(stack_num_table_rows)):
        #print(hex(program.mem_layout.stack_start_addr -8 - i), i, program.contexts[counter].stack.content[i])
        dpg.set_value(f'#stack_row_addr{col_idx:03}', f'{program.mem_layout.stack_start_addr -8 - i:#06x}:')
        dpg.set_value(f'#stack_row_val_hex{col_idx:03}', f'{program.contexts[counter].stack.content[i]:#04x}')
        dpg.set_value(f'#stack_row_val_dec{col_idx:03}', f'{program.contexts[counter].stack.content[i]:3}')

    dpg.unhighlight_table_row('#stack', rsp_row_idx)
    rsp_row_idx = stack_num_table_rows - abs(program.contexts[counter].regs.RSP - program.mem_layout.stack_start_addr)
    dpg.highlight_table_row('#stack', rsp_row_idx, [255, 0, 0, 100])




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

        dpg.set_item_pos('#num_insn_info_grp', pos=[vp_width - dpg.get_item_width('#num_insn_info_grp') - 110, vp_height - 30])

    # Callback to handle viewport resize event
    def viewport_resize_callback(sender, app_data):
        update_positions()


    # Start the Dear PyGui context
    dpg.create_context()

    dpg.configure_app(manual_callback_management=True)


    with dpg.font_registry():
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir)

        default_font = dpg.add_font(f'{ bundle_dir }/assets/Consolas.ttf', 15*2)


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
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        print("DIR:", bundle_dir)
        a = call(f'{ bundle_dir }/asemu { file_path }' + silencer, shell=True)
        program = des.get_executed_program()

        dpg.configure_item('#next', enabled=True)

        lines_of_code = [f'{ addr }:\t{ program.code.lines[i] }' for i, addr in enumerate(program.code.addresses)]
        dpg.configure_item(item="#code", items=lines_of_code, default_value=lines_of_code[program.contexts[counter].insn.index])

        reg_names = list(Registers.__dataclass_fields__.keys())[:-1]
        for i, key in enumerate(reg_names):
            dpg.set_value(f'#reg_val_col{i:02}', program.contexts[counter].regs.rdict[key])


        # for row_idx in range(stack_num_table_rows):
            # dpg.set_value(f'#stack_row_val_hex{row_idx:03}', '0xff')

        #  - len(program.contexts[counter].stack.content), stack_num_table_rows)
        for i, row_idx in enumerate(range(stack_num_table_rows)):
            dpg.set_value(f'#stack_row_addr{row_idx:03}', f'{program.mem_layout.stack_start_addr -8 - i:#06x}:')
            dpg.set_value(f'#stack_row_val_hex{row_idx:03}', f'{program.contexts[counter].stack.content[i]:#04x}')
            dpg.set_value(f'#stack_row_val_dec{row_idx:03}', f'{program.contexts[counter].stack.content[i]:3}')

        dpg.unhighlight_table_row('#stack', rsp_row_idx)
        rsp_row_idx = stack_num_table_rows - abs(program.contexts[counter].regs.RSP - program.mem_layout.stack_start_addr)
        dpg.highlight_table_row('#stack', rsp_row_idx, [255, 0, 0, 100])


    def cancel_callback(sender, app_data):
        print('Cancel was clicked.')
        print("Sender: ", sender)
        print("App Data: ", app_data)



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


        with dpg.child_window(autosize_x=True, autosize_y=True, border=False):

            with dpg.group(horizontal=True, height=700):

                with dpg.child_window(width=600, height=-1, no_scrollbar=True):

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Assembly code')
                        dpg.add_spacer(width=370)
                        dpg.add_button(label="Prev", enabled=False, callback=step, user_data=-1, tag='#prev')
                        dpg.add_button(label="Next", enabled=False, callback=step, user_data=1, tag='#next')

                    dpg.add_listbox(tag="#code", items=lines_of_code, width=-1, num_items=34, enabled=False)

                with dpg.child_window(width=275, height=-1, no_scrollbar=True):
                    dpg.add_text(default_value='Registers')
                    with dpg.table(header_row=False, row_background=True, no_host_extendX=True, policy=dpg.mvTable_SizingFixedFit):
                        dpg.add_table_column()
                        dpg.add_table_column()


                        reg_names = list(Registers.__dataclass_fields__.keys())[:-1]
                        for i, reg in enumerate(reg_names):
                            with dpg.table_row():
                                dpg.add_text(reg)
                                dpg.add_text('0xff', tag=f'#reg_val_col{i:02}')

                with dpg.child_window(width=275, height=-1, no_scrollbar=True):
                    dpg.add_text(default_value='Stack')

                    with dpg.table(tag='#stack', header_row=False, no_host_extendX=True,
                                row_background=True, resizable=False, policy=dpg.mvTable_SizingFixedFit,
                                scrollY=True):

                        dpg.add_table_column(width=-1, width_fixed=True)

                        for i in range(stack_num_table_rows):
                            with dpg.table_row():
                                with dpg.group(horizontal=True, indent=5):
                                    dpg.add_text('0x000000:', tag=f'#stack_row_addr{i:03}')
                                    dpg.add_spacer(width=50)
                                    dpg.add_text('0xff', tag=f'#stack_row_val_hex{i:03}')
                                    dpg.add_spacer(width=15)
                                    dpg.add_text('255', tag=f'#stack_row_val_dec{i:03}')

                        dpg.set_y_scroll('#stack', 999999)

        with dpg.group(tag='#num_insn_info_grp', height=-1, width=200, horizontal=True):
            dpg.add_text('Number of executed instructions: ')
            dpg.add_text('0', tag='#insn_cnt_info')







    # Start the Dear PyGui rendering loop
    dpg.create_viewport(title='Hohoemu', width=1650, height=800)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Set up the viewport resize callback
    dpg.set_viewport_resize_callback(viewport_resize_callback)
    # Adjust the window size on startup to fit the viewport
    update_positions()

    while dpg.is_dearpygui_running():
        jobs = dpg.get_callback_queue() # retrieves and clears queue
        dpg.run_callbacks(jobs)
        dpg.render_dearpygui_frame()


    dpg.start_dearpygui()
    dpg.destroy_context()
