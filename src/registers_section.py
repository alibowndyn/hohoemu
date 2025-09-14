from typing import TYPE_CHECKING
from utils import *
import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from gui import GUI



class RegisterWindow():
    '''The window that displays the registers.'''


    def __init__(self,
                 gui: 'GUI'):

        self.gui = gui
        '''A reference to the main GUI object.'''


        with dpg.child_window(auto_resize_x=True) as self.window:

            with dpg.group(horizontal=True):
                dpg.add_text(default_value='Registers')
                dpg.add_spacer(width=15)
                dpg.add_button(label="Open all", enabled=True, callback=self.show_all_subregs)
                dpg.add_button(label="Collapse all", enabled=True, callback=self.hide_all_subregs)

            dpg.add_separator()

            with dpg.table(tag='#regs', header_row=False, row_background=False,
                            policy=dpg.mvTable_SizingFixedFit, scrollX=True):

                dpg.add_table_column()
                dpg.add_table_column()
                dpg.add_table_column()

                for reg in main_regs:
                    with dpg.table_row():

                        dpg.add_selectable(label=reg, indent=5, span_columns=True, callback=self.show_register_parts, user_data=reg)
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

            self.show_register_parts(None, None, 'RFLAGS')


    def show_register_parts(self, sender, app_data, user_data):
        '''Shows the subparts of a register.'''

        for reg_part in reg_subparts[user_data]:
            table_row = f'#{ reg_part }_hidden'

            if not dpg.is_item_shown(table_row):
                dpg.show_item(table_row)
            else:
                dpg.hide_item(table_row)

    def show_all_subregs(self):
        '''Shows all the subregisters.'''

        for reg in main_regs:
            for reg_part in reg_subparts[reg]:
                dpg.show_item(f'#{ reg_part }_hidden')

    def hide_all_subregs(self):
        '''Hides all the subregisters.'''

        for reg in main_regs[:-1]:
            for reg_part in reg_subparts[reg]:
                dpg.hide_item(f'#{ reg_part }_hidden')

    def update_register_values(self):
        '''Updates the values of the registers.'''

        for reg in main_regs:
            val = self.gui.program.get_current_context().regs.rdict[reg]

            dpg.set_item_label(f'#{ reg }_val_hex', f'{val:#x}')
            dpg.set_item_label(f'#{ reg }_val_dec', val)

            for j in range(len(reg_subparts[reg])):
                reg_part = reg_subparts[reg][j]

                if reg_part in flags:
                    val = self.gui.program.get_flag(reg_part)
                else:
                    val = self.gui.program.get_current_context().regs.rdict[reg_part]

                dpg.set_value(f'#{ reg_part }_val_hex', f'{val:#x}')
                dpg.set_value(f'#{ reg_part }_val_dec', f'{val}  ')
