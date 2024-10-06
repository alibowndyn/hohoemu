from typing import TYPE_CHECKING
from emu_dataclasses import MemorySegment, Symbol
from utils import *
import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from gui import GUI



class SymbolsWindow():
    '''The window that displays the registers.'''

    _symbol_selectable_tags: dict[str, list[int]] = { 'rodata': [], 'data': [], 'bss': [] }
    '''The tags of the selectable widgets for each segment.'''
    _sym_byte_group_tags: dict[str, dict[str, list[int]]] = { 'rodata': {}, 'data': {}, 'bss': {} }
    '''The tags of the group widgets containing the bytes for each symbol.'''


    def __init__(self,
                 gui: 'GUI'):

        self.gui = gui
        '''A reference to the main GUI object.'''


        with dpg.child_window(width=400, border=True, resizable_x=True, no_scrollbar=True, no_scroll_with_mouse=True):

            dpg.add_text(default_value='Static data symbols')
            dpg.add_separator()

            with dpg.table(header_row=False, row_background=False, resizable=False,
                           no_host_extendX=True, scrollY=True):

                dpg.add_table_column()

                with dpg.table_row():
                    with dpg.collapsing_header(label=".rodata", tag='rodata', default_open=True):
                        pass

                with dpg.table_row():
                    with dpg.collapsing_header(label=".data", tag='data', default_open=True):
                        pass

                with dpg.table_row():
                    with dpg.collapsing_header(label=".bss", tag='bss', default_open=True):
                        pass


    def build_symbol_widgets(self, segment: MemorySegment):
        '''Builds the widgets for the symbols in the given segment.'''

        for sym_name in self._sym_byte_group_tags[segment.name]:
            for group_tag in self._sym_byte_group_tags[segment.name][sym_name]:
                if dpg.does_item_exist(group_tag):
                    dpg.delete_item(group_tag)
            self._sym_byte_group_tags[segment.name][sym_name].clear()

        for sel_tag in self._symbol_selectable_tags[segment.name]:
            if dpg.does_item_exist(sel_tag):
                dpg.delete_item(sel_tag)

        for sym in segment.symbols:
            sel = dpg.add_selectable(label=sym.name, parent=segment.name, indent=5, span_columns=True, callback=self.show_symbol_parts, user_data=(segment.name, sym.name))
            self._symbol_selectable_tags[segment.name].append(sel)

            self._sym_byte_group_tags[segment.name][sym.name] = []

            for i, byte in enumerate(sym.bytes):
                with dpg.group(parent=segment.name, horizontal=True, show=False, horizontal_spacing=80) as sym_byte_group:

                    self._sym_byte_group_tags[segment.name][sym.name].append(sym_byte_group)

                    addr = dpg.add_text(f'{sym.addr + i:#08x}:', indent=20)
                    dpg.bind_item_theme(addr, self.gui.addr_text_theme)

                    dpg.add_text(f'{byte:#04x}', tag=f'{ segment.name }_{ sym.name }_byte_{ i }_hex')
                    dpg.add_text(byte, tag=f'{ segment.name }_{ sym.name }_byte_{ i }_dec')

    def show_symbol_parts(self, sender, app_data, user_data: tuple[str, str]):
        seg_name, sym_name = user_data[0], user_data[1]

        for group_tag in self._sym_byte_group_tags[seg_name][sym_name]:
            if dpg.is_item_shown(group_tag):
                dpg.hide_item(group_tag)
            else:
                dpg.show_item(group_tag)

    def update_symbols_window(self):
        ctx = self.gui.program.get_current_context()
        segments = [ctx.dynamic_mem.data, ctx.dynamic_mem.bss]

        for seg in segments:
            for sym in seg.symbols:
                for i, byte in enumerate(sym.bytes):
                    dpg.set_value(f'{ seg.name }_{ sym.name }_byte_{ i }_hex', f'{byte:#04x}')
                    dpg.set_value(f'{ seg.name }_{ sym.name }_byte_{ i }_dec', byte)
