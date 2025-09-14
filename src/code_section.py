from typing import TYPE_CHECKING
from utils import *
import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from gui import GUI



class CodeWindow():
    '''The window that displays the assembly code.'''

    code_table: int = 0
    '''The tag of the table containing the assembly instructions.'''
    row_tags: list[int] = []
    '''The tags of the rows of the table containing the assembly instructions.'''
    address_tags: list[int] = []
    '''The tags of the selectable widgets containing the addresses of the assembly instructions.'''
    text_tags: list[int] = []
    '''The tags of the text widgets containing the assembly instructions.'''
    emulation_failed_modal: int = 0
    '''The tag of the modal window that appears when the emulation fails.'''
    row_height: int = 25
    '''The height of a row in the code table.'''
    highlighted_row_idx: int  = 0
    '''The index of the currently highlighted row in the code table.'''
    highlighted_code_row_color: tuple[int, int, int, int] = (160, 22, 49, 200)
    '''The color of the highlighted row in the code table.'''
    breakpoints: list[tuple[int, str]] = []
    '''The list of breakpoints in the code.
       A breakpoint is a tuple containing the tag of the selectable widget holding the address
       and the address of the instruction.'''


    def __init__(self,
                 gui: 'GUI'):

        self.gui = gui
        '''A reference to the main GUI object.'''


        with dpg.child_window(auto_resize_x=True) as self.window:

            with dpg.group(horizontal=True):

                dpg.add_text(default_value='Assembly code')
                dpg.add_spacer(width=15)
                dpg.add_button(label="Previous", tag='#prev', callback=self.gui.step, user_data=-1)
                dpg.add_button(label="Next", tag='#next', callback=self.gui.step, user_data=1)
                dpg.add_button(label="Continue", tag='#cont', callback=self.gui.continue_until_breakpoint, user_data=1)
                dpg.add_button(label="Reset", tag='#reset', callback=self.gui.reset)

            dpg.add_separator()

            with dpg.tab_bar():
                with dpg.tab(label='Assembly code') as self.assembly_code_tab:
                    pass

                with dpg.tab(label='Raw code'):
                    with dpg.child_window(border=False):
                        self.raw_assembly_text = dpg.add_text()


    def build_code_table(self):
        '''Builds the table containing the instructions extracted by the emulator's preprocessor.'''

        with dpg.table(parent=self.assembly_code_tab, header_row=False, row_background=False, scrollX=True,
                       resizable=False, policy=dpg.mvTable_SizingFixedFit) as self.code_table:

            dpg.add_table_column()
            dpg.add_table_column()

            for line, address in zip(self.gui.program.code.lines, self.gui.program.code.addresses):
                with dpg.table_row(parent=self.code_table) as row:

                    self.row_tags.append(row)

                    addr = dpg.add_selectable(label=f'{address:#08x}:', callback=self.set_breakpoint)
                    dpg.set_item_user_data(item=addr, user_data=addr)
                    dpg.bind_item_theme(addr, self.gui.addr_selectable_theme)
                    self.address_tags.append(addr)

                    text = dpg.add_text(line)
                    self.text_tags.append(text)

    def show_error_message(self):
        '''Shows an error message when the emulation fails.'''

        if not dpg.does_item_exist(self.emulation_failed_modal):
            pos = calculate_dialog_position(350, 150)
            with dpg.window(label='Error', min_size=[350, 150], pos=pos, show=False,
                            modal=True, no_resize=True, no_move=True) as self.emulation_failed_modal:

                dpg.add_text("The software cannot emulate this source code. Sorry!", color=[255, 0, 0], bullet=True, wrap=300)
                dpg.add_button(label='  OK  ', pos=[15, 100], callback=lambda: dpg.hide_item(self.emulation_failed_modal))

        if dpg.is_item_shown(self.emulation_failed_modal):
            dpg.hide_item(self.emulation_failed_modal)
        else:
            dpg.show_item(self.emulation_failed_modal)

    def reset_code_window(self):
        '''Resets the code window to a clean state.'''

        if dpg.does_item_exist(self.code_table):
            dpg.delete_item(self.code_table)

        self.breakpoints.clear()

        self.highlighted_row_idx = 0
        self.row_tags.clear()
        self.address_tags.clear()
        self.text_tags.clear()

    def initialize_code_window(self):
        '''Initializes the code window.'''

        self.reset_code_window()

        self.build_code_table()
        self.update_code_window()

        raw_assembly = open(self.gui.file_path, 'r').read()
        dpg.set_value(self.raw_assembly_text, raw_assembly)


    def update_code_window(self):
        '''Updates the code window to match the current execution context.'''

        dpg.unhighlight_table_row(self.code_table, row=self.highlighted_row_idx)

        # color the previously highlighted row's address text back to address theme
        dpg.bind_item_theme(self.address_tags[self.highlighted_row_idx], theme=self.gui.addr_selectable_theme)

        self.highlighted_row_idx = self.gui.program.get_current_context().insn.index
        dpg.highlight_table_row(self.code_table, row=self.highlighted_row_idx, color=self.highlighted_code_row_color)

        # color the highlighted row's address text to white so it can be seen better
        dpg.bind_item_theme(self.address_tags[self.highlighted_row_idx], theme=self.gui.white_text)

        for bp in self.breakpoints:
            dpg.bind_item_theme(bp[0], theme=self.gui.break_point_theme)

        self.update_code_window_scroll_position(self.highlighted_row_idx)

    def update_code_window_scroll_position(self, row_idx: int):
        # only do the calculations if the the row is not visible
        if dpg.is_item_visible(self.address_tags[self.highlighted_row_idx]):
            return

        row_y = self.highlighted_row_idx * self.row_height

        # if row_y is closer to the top of the code window, scroll to the top, else scroll to the bottom
        if row_y < dpg.get_viewport_client_height() - row_y:
            scroll_height = 0
        else:
            scroll_height = self.row_height * self.gui.program.contexts[len(self.gui.program.contexts) - 1].insn.index

        dpg.set_y_scroll(self.code_table, scroll_height)

    def set_breakpoint(self, sender, app_data, user_data):
        dpg.bind_item_theme(item=user_data, theme=self.gui.break_point_theme)

        addr_text = int(dpg.get_item_label(user_data)[:-1], 16)
        bp = (user_data, addr_text)

        if bp in self.breakpoints:
            self.breakpoints.remove(bp)

            is_highlighted_row = user_data == self.address_tags[self.highlighted_row_idx]
            if is_highlighted_row:
                dpg.bind_item_theme(item=user_data, theme=self.gui.white_text)
            else:
                dpg.bind_item_theme(item=user_data, theme=self.gui.addr_selectable_theme)
        else:
            self.breakpoints.append(bp)

        sorted(self.breakpoints, key=lambda x: x[1])

    def indicate_program_end(self):
        if not dpg.does_item_exist(self.code_table):
            return

        if not dpg.does_item_exist("program_end_row_1"):
            with dpg.table_row(parent=self.code_table, height=100, tag="program_end_row_1"):
                pass

        if not dpg.does_item_exist("program_end_row_2"):
            with dpg.table_row(parent=self.code_table, tag="program_end_row_2"):
                dpg.add_text("Execution done.", color=(255, 0, 0, 255), wrap=90)

        if self.gui.program_ended:
            dpg.show_item("program_end_row_1")
            dpg.show_item("program_end_row_2")
            dpg.set_y_scroll(self.code_table, 999999)
        else:
            dpg.hide_item("program_end_row_1")
            dpg.hide_item("program_end_row_2")
