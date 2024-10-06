from typing import TYPE_CHECKING
from utils import *
import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from gui import GUI



class MainMenuBar():
    '''The main menu bar of the GUI.'''

    _file_dialog_modal_width: int = 800
    '''The width of the file dialog modal window.'''
    _file_dialog_modal_height: int = 600
    '''The height of the file dialog modal window.'''
    _help_container_window: int = 0
    '''The tag of the help dialog container window.'''
    _assembly_file_color: tuple[int, int, int, int] = (0, 255, 0, 255)
    '''The color of assembly files in the file dialog.'''
    _normal_file_color: tuple[int, int, int, int] = (150, 255, 150, 255)
    '''The color of normal files in the file dialog.'''


    def __init__(self,
                 gui: 'GUI'):

        self.gui = gui
        '''A reference to the main GUI object.'''


        with dpg.viewport_menu_bar():

            with dpg.menu(label='File'):

                dpg.add_menu_item(label='Load assembly file', callback=self.show_file_dialog)

            with dpg.menu(label='About'):
                dpg.add_menu_item(label='Help', callback=self.show_help_dialog)


    def show_file_dialog(self):
        '''Shows a file dialog for loading an assembly file.'''

        center_pos = calculate_dialog_position(self._file_dialog_modal_width, self._file_dialog_modal_height)
        with dpg.child_window(show=False, parent=self.gui.main_window, pos=center_pos) as self.modal_container_window:

            with dpg.file_dialog(modal=True, directory_selector=False,
                                 min_size=[self._file_dialog_modal_width, self._file_dialog_modal_height],
                                 callback=self.gui.load_assembly_file):

                dpg.add_file_extension(".s", color=self._assembly_file_color, custom_text="[Assembly]")
                dpg.add_file_extension("", color=self._normal_file_color)
                dpg.add_file_extension(".*")

    def show_help_dialog(self):
        '''Shows a help dialog with information about the GUI, including how to use it.'''

        if not dpg.does_item_exist(self._help_container_window):

            pos = calculate_dialog_position(800, 600)
            with dpg.window(label='Help', min_size=[200, 100], pos=pos, show=False,
                            modal=True, no_resize=True, no_move=True) as self._help_container_window:

                with dpg.group():

                    dpg.add_text(wrap=500, bullet=True, default_value='To load an assembly file, click on "File" -> "Load assembly file".')
                    dpg.add_text(wrap=500, bullet=True, default_value='The program will be loaded and the GUI will display the assembly code, registers, stack, and symbols.')
                    dpg.add_text(wrap=500, bullet=True, default_value='You can step through the code by clicking on "Previous" and "Next" or pressing the up and down arrow keys.')
                    dpg.add_text(wrap=500, bullet=True, default_value='You can also continue the execution until a breakpoint by clicking on "Continue" or pressing the right arrow key.')
                    dpg.add_text(wrap=500, bullet=True, default_value='You can reset the program by clicking on "Reset" or pressing the left arrow key.')
                    dpg.add_text(wrap=500, bullet=True, default_value='You can set breakpoints by clicking on the address of an instruction.')
                    dpg.add_text(wrap=500, bullet=True, default_value='The GUI will highlight the next instruction about to be executed and also highlight the stack row corresponding to the RSP register.')
                    dpg.add_text(wrap=500, bullet=True, default_value='The GUI will also display the symbols in the program and the values of the registers and stack.')
                    dpg.add_text(wrap=500, bullet=True, default_value='You can resize each section of the GUI by dragging the borders of the windows. Double clcking the borders of the windows automatically resizes them to fit their contents.')
                    dpg.add_text(wrap=500, bullet=True, default_value='You can also collapse and expand the registers and symbols sections by clicking on the registers\' names or the symbol\'s name.')
                    dpg.add_spacer(height=15)
                    dpg.add_button(label="Close", callback=lambda: dpg.hide_item(self._help_container_window))


        if dpg.is_item_shown(self._help_container_window):
            dpg.hide_item(self._help_container_window)
        else:
            dpg.show_item(self._help_container_window)
