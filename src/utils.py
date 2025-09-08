import os
import sys
import dearpygui.dearpygui as dpg



main_regs = (
    'RAX', 'RBX', 'RCX', 'RDX', 'RSI', 'RDI',
    'RBP', 'RSP', 'R8', 'R9', 'R10', 'R11',
    'R12', 'R13', 'R14', 'R15', 'RIP', 'RFLAGS',
)

flags = ('CF', 'PF', 'ZF', 'SF', 'OF')
'''The flags in the RFLAGS register.'''

reg_subparts = {
    'RAX': ('EAX', 'AX', 'AH', 'AL'),
    'RBX': ('EBX', 'BX', 'BH', 'BL'),
    'RCX': ('ECX', 'CX', 'CH', 'CL'),
    'RDX': ('EDX', 'DX', 'DH', 'DL'),
    'RSI': ('ESI', 'SI', 'SIL'),
    'RDI': ('EDI', 'DI', 'DIL'),
    'RBP': ('EBP', 'BP', 'BPL'),
    'RSP': ('ESP', 'SP', 'SPL'),
    'R8':  ('R8D', 'R8W', 'R8B'),
    'R9':  ('R9D', 'R9W', 'R9B'),
    'R10': ('R10D', 'R10W', 'R10B'),
    'R11': ('R11D', 'R11W', 'R11B'),
    'R12': ('R12D', 'R12W', 'R12B'),
    'R13': ('R13D', 'R13W', 'R13B'),
    'R14': ('R14D', 'R14W', 'R14B'),
    'R15': ('R15D', 'R15W', 'R15B'),
    'RIP': ('EIP', 'IP'),
    'RFLAGS': flags,
}
'''A mapping of the register names to their subparts.'''

irrelevant_symbols = ('_IO_stdin_used', '__data_start', '__dso_handle', 'completed.0')


def get_program_dir():
    '''Returns the directory the program is running from.'''

    if getattr(sys, 'frozen', False):
        # we are running in a bundle created by PyInstaller
        return sys._MEIPASS
    else:
        # we are running in a normal Python environment
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def calculate_dialog_position(width: int, height: int) -> tuple[int, int]:
    '''Calculates the position of a dialog window based on the viewport size.'''

    pos_x = (dpg.get_viewport_width() // 2) - (width // 2)
    pos_y = (dpg.get_viewport_height() // 2) - (height // 2)

    return (pos_x, pos_y)
