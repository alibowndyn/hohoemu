from typing import TYPE_CHECKING
import subprocess
from emu_dataclasses import *
from deserializer import *
from utils import *
from menubar import MainMenuBar
from code_section import CodeWindow
from registers_section import RegisterWindow
from stack_section import StackWindow
from symbols_section import SymbolsWindow
import dearpygui.dearpygui as dpg


FONT_SCALE = 3
MIN_WIDTH = 1280
MIN_HEIGHT = 720



class GUI:
    '''A class that represents the GUI of the emulator.'''

    file_path: str = ""
    '''The path of the opened assembly file.'''
    insn_counter: int = 0
    '''The number of instructions executed so far.'''
    program: ExecutedProgram = None
    '''The executed program.'''
    mem_addr_tags = []
    '''Tags of the widgets containing memory addresses.'''
    _main_color_theme: tuple[int, int, int] = (22, 160, 133)
    '''The main color theme of the GUI.'''
    _addr_color_theme: tuple[int, int, int] = (255, 87, 51)
    '''The color theme for memory addresses.'''
    program_ended: bool = False
    '''Indicates whether the program has ended.'''


    def __init__(self,
                 width: int,
                 height: int):

        self.program_dir = get_program_dir()
        '''The path of the directory containing the program's executable.'''

        dpg.create_context()
        dpg.create_viewport(title='Hohoemu', width=width, min_width=MIN_WIDTH, height=height, min_height=MIN_HEIGHT)
        dpg.set_viewport_resize_callback(self.viewport_resize_callback)


        # load font asset
        with dpg.font_registry():
            default_font = dpg.add_font(f'{ self.program_dir }/assets/Consolas.ttf', 18*FONT_SCALE)

        dpg.set_global_font_scale(1/FONT_SCALE)
        dpg.bind_font(default_font)

        # create themes for the GUI
        self.create_themes()

        # register keyboard and mouse handlers
        with dpg.handler_registry():
            dpg.add_key_press_handler(dpg.mvKey_Down, callback=self.step, user_data=1)
            dpg.add_key_press_handler(dpg.mvKey_Up, callback=self.step, user_data=-1)
            dpg.add_key_press_handler(dpg.mvKey_Right, callback=self.continue_until_breakpoint)
            dpg.add_key_press_handler(dpg.mvKey_Left, callback=self.reset)


        with dpg.window(tag='#main_window', pos=[0,0], no_resize=True,
            no_title_bar=True, horizontal_scrollbar=True, no_move=True) as self.main_window:

            # set up the main menu bar
            self.main_menubar = MainMenuBar(self)

            with dpg.group(horizontal=True):

                self.code_section = CodeWindow(self)
                self.register_section = RegisterWindow(self)
                self.stack_section = StackWindow(self)
                self.symbols_section = SymbolsWindow(self)

        self.bind_themes()


        # start the Dear PyGui rendering loop
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # resize everything on the 1st frame
        dpg.set_frame_callback(1, self.viewport_resize_callback)


        dpg.start_dearpygui()
        dpg.destroy_context()

    def viewport_resize_callback(self, sender, app_data):
        dpg.set_item_width(self.main_window, width=dpg.get_viewport_width())
        dpg.set_item_height(self.main_window, height=dpg.get_viewport_height())


    def get_assembly_file(self, sender, app_data):
        '''Acts as the callback function of the file modal dialog.'''

        # delete the file dialog's container window, which was used to center the file dialog
        dpg.delete_item(self.main_menubar.modal_container_window)

        self.file_path = app_data['file_path_name']
        self.load_assembly_file()

    def load_assembly_file(self):
        '''Loads and emulates the chosen assembly source file.'''

        # we clicked on 'Reload file' while no file was loaded into our program
        if self.file_path == "":
            return

        return_code = subprocess.call(f'{ self.program_dir }/asemu { self.file_path }',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if return_code != 0:
            self.code_section.show_error_message()
            self.file_path = ""
            return

        try:
            self.program = Deserializer().get_executed_program()
        except Exception as ex:
            print(ex)

        self.program_ended = False
        self.initialize_section_windows()

        dpg.configure_item(item=self.code_section.window, auto_resize_x=False, resizable_x=True)

    def initialize_section_windows(self):
        '''Initializes all the section windows of the GUI.'''

        # initialize the code, register, and stack sections
        self.code_section.initialize_code_window()
        self.register_section.update_register_values()
        self.stack_section.update_stack_window()

        # initialize the symbols section
        self.symbols_section.build_symbol_widgets(self.program.static_mem.rodata)
        self.symbols_section.build_symbol_widgets(self.program.get_current_context().dynamic_mem.data)
        self.symbols_section.build_symbol_widgets(self.program.get_current_context().dynamic_mem.bss)

    def step(self, sender, app_data, user_data: int):
        '''Steps through the program forward or backwad by one instruction at a time.'''

        self.code_section.indicate_program_end()

        ret = 0
        if self.program is None or (ret := self.program.step(user_data)) > 0:
            self.program_ended = ret == 2
            self.code_section.indicate_program_end()
            return

        self.program_ended = False

        self.code_section.update_code_window()
        self.register_section.update_register_values()

        # update the stack window if the stack pointer has changed
        #if self.stack_section.rsp != self.program.get_current_context().regs.RSP:
        self.stack_section.update_stack_window()

        self.symbols_section.update_symbols_window()

    def continue_until_breakpoint(self):
        '''Continues the program execution until a breakpoint is reached.'''

        breakpoints = self.code_section.breakpoints
        if not breakpoints or self.program_ended:
            return

        highlighted_row_idx = self.code_section.highlighted_row_idx
        addrasses = [bp[1] for bp in breakpoints]
        tmp_addrasses = addrasses.copy() #important
        highlighted_row_addr = self.program.code.addresses[highlighted_row_idx]

        if highlighted_row_addr in addrasses:
            tmp_addrasses.remove(highlighted_row_addr) #important

        reached = False
        while not reached and not self.program_ended:
            if self.program.code.addresses[self.code_section.highlighted_row_idx] not in tmp_addrasses:
                self.step(None, None, 1)
                tmp_addrasses = [bp[1] for bp in breakpoints] #important
            else:
                reached = True

    def reset(self):
        '''Resets the program to its initial state.'''

        if self.program is None or self.program.index == 0:
            return

        self.program_ended = False
        self.program.index = 0

        self.code_section.update_code_window()
        self.register_section.update_register_values()
        self.stack_section.update_stack_window()
        self.symbols_section.update_symbols_window()


    def create_themes(self):
        '''Creates the themes for the GUI.'''

        # Create a theme for the main window
        with dpg.theme() as self.main_window_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (*self._main_color_theme, 180), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 1)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (255, 255, 255, 50))  # Black border
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)

            with dpg.theme_component(dpg.mvSelectable):
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)
                # this will make sure that clicking a selectable won't change its color
                dpg.add_theme_color(dpg.mvThemeCol_Header, (37, 37, 38, -255), category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvCollapsingHeader):
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvTab):
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (*self._main_color_theme, 100), category=dpg.mvThemeCat_Core)


        # Create a theme for the texts showing memory addresses
        with dpg.theme() as self.addr_sel_theme:
            with dpg.theme_component(dpg.mvSelectable):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 150, 22, 255), category=dpg.mvThemeCat_Core)

        with dpg.theme() as self.break_point_theme:
            with dpg.theme_component(dpg.mvSelectable):
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (255, 22, 22, 200), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (255, 22, 22, 200), category=dpg.mvThemeCat_Core)
                # this will make sure that clicking a selectable won't change its color
                dpg.add_theme_color(dpg.mvThemeCol_Header, (255, 22, 22, 200), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)

        with dpg.theme() as self.default_selectable:
            with dpg.theme_component(dpg.mvSelectable):
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (*self._main_color_theme, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (*self._main_color_theme, 255), category=dpg.mvThemeCat_Core)
                # this will make sure that clicking a selectable won't change its color
                dpg.add_theme_color(dpg.mvThemeCol_Header, (*self._main_color_theme, -255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (*self._main_color_theme, 255), category=dpg.mvThemeCat_Core)

        with dpg.theme() as self.addr_text_theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (*self._addr_color_theme, 200), category=dpg.mvThemeCat_Core)

        with dpg.theme() as self.addr_selectable_theme:
            with dpg.theme_component(dpg.mvSelectable):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (*self._addr_color_theme, 200), category=dpg.mvThemeCat_Core)

        with dpg.theme() as self.white_text:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255), category=dpg.mvThemeCat_Core)

    def bind_themes(self):
        '''Binds the created themes to the GUI components.'''

        dpg.bind_item_theme(self.main_window, self.main_window_theme)
