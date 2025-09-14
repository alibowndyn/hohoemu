from typing import TYPE_CHECKING
from utils import *
import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from gui import GUI



class MainMenuBar():
    '''The main menu bar of the GUI.'''

    _help_text: list[str] = None
    '''Help text which populates the Help modal window.'''
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


        with dpg.menu_bar():

            with dpg.menu(label='File'):

                dpg.add_menu_item(label='Load assembly file', callback=self.show_file_dialog)
                dpg.add_menu_item(label='Reload file', callback=self.gui.load_assembly_file)

            with dpg.menu(label='About'):
                dpg.add_menu_item(label='Help', callback=self.show_help_dialog)


    def show_file_dialog(self):
        '''Shows a file dialog for loading an assembly file.'''

        center_pos = calculate_dialog_position(self._file_dialog_modal_width, self._file_dialog_modal_height)
        with dpg.child_window(show=False, parent=self.gui.main_window, pos=center_pos) as self.modal_container_window:

            with dpg.file_dialog(modal=True, directory_selector=False,
                                 min_size=[self._file_dialog_modal_width, self._file_dialog_modal_height],
                                 callback=self.gui.get_assembly_file):

                dpg.add_file_extension(".s", color=self._assembly_file_color, custom_text="[Assembly]")
                dpg.add_file_extension("", color=self._normal_file_color)
                dpg.add_file_extension(".*")

    def show_help_dialog(self):
        '''Shows a help dialog with information about the GUI, including how to use it.'''

        pos = calculate_dialog_position(800, 600)

        if self._help_text is None:
            self._help_text = open(f'{ self.gui.program_dir }/assets/helptext.txt', 'r').read().splitlines()

        with dpg.window(label='Help', min_size=[200, 100], pos=pos, show=False,
                        modal=True, no_resize=True) as self._help_container_window:

            with dpg.group():

                for line in self._help_text:
                    dpg.add_text(wrap=800, bullet=line != "", default_value=line)

                dpg.add_spacer(height=15)
                dpg.add_button(label="Close", callback=lambda: dpg.hide_item(self._help_container_window))


        if dpg.is_item_shown(self._help_container_window):
            dpg.hide_item(self._help_container_window)
        else:
            dpg.show_item(self._help_container_window)
