from typing import TYPE_CHECKING
from utils import *
import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from gui import GUI



class StackWindow():
    '''The window that displays the stack.'''

    _num_stack_rows: int = 128
    '''The number of rows in the stack table.'''


    def __init__(self,
                 gui: 'GUI'):

        self.gui = gui
        '''A reference to the main GUI object.'''
        self.rsp: int = 0
        '''The value of the RSP register.'''
        self.rsp_row_highlight_color: tuple[int, int, int, int] = (160, 22, 49, 200)
        '''The color of the highlighted row in the stack table.'''
        self.rsp_row_idx = self._num_stack_rows - 8
        '''The index of the highlighted row in the stack table.'''


        with dpg.child_window(auto_resize_x=True):
                dpg.add_text('Stack')

                dpg.add_separator()
                with dpg.table(header_row=False, no_host_extendX=True,
                            row_background=True, resizable=False, policy=dpg.mvTable_SizingFixedFit,
                            scrollY=True) as self.stack_table:

                    dpg.add_table_column(width=-1, width_fixed=True)

                    for i in range(self._num_stack_rows):
                        with dpg.table_row():

                            with dpg.group(horizontal=True, indent=5):

                                addr = dpg.add_text('0x000000:', tag=f'#stack_row_addr{i:03}')
                                dpg.bind_item_theme(addr, self.gui.addr_text_theme)

                                dpg.add_spacer(width=30)
                                dpg.add_text('0xff', tag=f'#stack_row_val_hex{i:03}')

                                dpg.add_spacer(width=15)
                                dpg.add_text('255  ', tag=f'#stack_row_val_dec{i:03}')

                    dpg.set_y_scroll(self.stack_table, 999999)

    def update_stack_window(self):
        ctx = self.gui.program.get_current_context()

        for i, row_idx in enumerate(range(self._num_stack_rows)):
            dpg.set_value(f'#stack_row_addr{row_idx:03}', f'{self.gui.program.mem_layout.stack_start_addr - 128 + i:#06x}:')
            dpg.set_value(f'#stack_row_val_hex{row_idx:03}', f'{ctx.stack.content[i]:#04x}')
            dpg.set_value(f'#stack_row_val_dec{row_idx:03}', f'{ctx.stack.content[i]:3}  ')

            # reset the previously highlighted row and bind the default theme to its address
            dpg.unhighlight_table_row(self.stack_table, self.rsp_row_idx)
            dpg.bind_item_theme(f'#stack_row_addr{self.rsp_row_idx:03}', theme=self.gui.addr_text_theme)

            self.rsp = ctx.regs.RSP
            self.rsp_row_idx = self._num_stack_rows - abs(self.rsp - self.gui.program.mem_layout.stack_start_addr)

            # highlight the new row and bind the white theme to its address
            dpg.highlight_table_row(self.stack_table, self.rsp_row_idx, self.rsp_row_highlight_color)
            dpg.bind_item_theme(f'#stack_row_addr{self.rsp_row_idx:03}', theme=self.gui.white_text)
            dpg.focus_item(f'#stack_row_addr{self.rsp_row_idx:03}')
