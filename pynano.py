import os
import sys
from msvcrt import getch

debug = True
tab_equivalent_length = 4

cursor = [0, 0]
modified = False
show_save_menu = False
terminal_size = os.get_terminal_size()
encoding = 'utf-8'

# snippets from stackoverflow, like fine art in the trash

import errno
import tempfile

ERROR_INVALID_NAME = 123


def is_pathname_valid(pathname: str) -> bool:
    '''
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    '''
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)  # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError as exc:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.
    #
    # Did we mention this should be shipped with Python already?


def is_path_sibling_creatable(pathname: str) -> bool:
    '''
    `True` if the current user has sufficient permissions to create **siblings**
    (i.e., arbitrary files in the parent directory) of the passed pathname;
    `False` otherwise.
    '''
    # Parent directory of the passed path. If empty, we substitute the current
    # working directory (CWD) instead.
    dirname = os.path.dirname(pathname) or os.getcwd()

    try:
        # For safety, explicitly close and hence delete this temporary file
        # immediately after creating it in the passed path's parent directory.
        with tempfile.TemporaryFile(dir=dirname):
            pass
        return True
    # While the exact type of exception raised by the above function depends on
    # the current version of the Python interpreter, all such types subclass the
    # following exception superclass.
    except EnvironmentError:
        return False


def is_path_exists_or_creatable_portable(pathname: str) -> bool:
    '''
    `True` if the passed pathname is a valid pathname on the current OS _and_
    either currently exists or is hypothetically creatable in a cross-platform
    manner optimized for POSIX-unfriendly filesystems; `False` otherwise.

    This function is guaranteed to _never_ raise exceptions.
    '''
    try:
        # To prevent "os" module calls from raising undesirable exceptions on
        # invalid pathnames, is_pathname_valid() is explicitly called first.
        return is_pathname_valid(pathname) and (os.path.exists(pathname) or is_path_sibling_creatable(pathname))
    # Report failure on non-fatal filesystem complaints (e.g., connection
    # timeouts, permissions issues) implying this path to be inaccessible. All
    # other exceptions are unrelated fatal issues and should not be caught here.
    except OSError:
        return False


def save_file(filename, content):
    content[-1] = content[-1][:-1]  # remove EOF symbol
    with open(filename, 'w') as f:
        f.write(''.join(content))


def show_screen(content):
    global show_save_menu, cursor
    os.system('cls')
    print('\tpynano v0.1')
    print('-' * terminal_size.columns, end='')
    for i, line in enumerate(content):
        for j, char in enumerate(line):
            if [i, j] == cursor:
                print('\033[4;30;47m{}\033[0m{}'.format(
                    *((' \n', '') if char == '\n' else (' ', ' ' * (tab_equivalent_length - 1)) if char == '\t' else (' ', '') if char == '\x00' else (char,
                                                                                                                                                       ''))),
                      end='')
            else:
                print(' ' * tab_equivalent_length if char == '\t' else ' ' if char == '\x00' else char, end='')
    print('\n~' * (terminal_size.lines - len(content) - 6 - debug * (1 + len(content))))

    # print(terminal_size.lines - len(content) - 2 * int(show_save_menu) - 4)
    if show_save_menu:
        print('Save change? (Y/N) | C-c to cancel')
        while True:
            key = getch()
            if key == b'\x03':
                show_save_menu = False
                show_screen(content)
                return
            elif key == b'Y' or key == b'y':
                show_save_menu = False
                # show_save_title = True
                filename = get_filename()
                save_file(filename, content)
                my_exit()
            elif key == b'N' or key == b'n':
                # TODO save file to tmp
                my_exit()
    else:
        print('C-x to save | C-c to exit')
    if debug:
        print(cursor)
        print(content)


def get_filename():
    return target_path


def cursor_left(content, cursor):
    if cursor[1] == 0:
        if cursor[0] != 0:
            cursor[0] = max(0, cursor[0] - 1)
            cursor[1] = len(content[cursor[0]]) - 1
    else:
        cursor[1] -= 1
    return content, cursor


def cursor_right(content, cursor):
    if cursor[1] == len(current_line) - 1:
        if cursor[0] != len(content) - 1:
            cursor[0] = min(len(content) - 1, cursor[0] + 1)
            cursor[1] = 0
    else:
        cursor[1] += 1
    return content, cursor


def cursor_up(content, cursor):
    cursor[0] = max(0, cursor[0] - 1)
    cursor[1] = min(len(content[cursor[0]]) - 1, cursor[1])
    return content, cursor


def cursor_down(content, cursor):
    cursor[0] = min(len(content) - 1, cursor[0] + 1)
    cursor[1] = min(len(content[cursor[0]]) - 1, cursor[1])
    return content, cursor


def cursor_to_start(content, cursor):
    cursor[1] = 0
    return content, cursor


def cursor_to_end(content, cursor):
    cursor[1] = len(current_line) - 1
    return content, cursor


def delete(content, cursor):
    global modified
    modified = True
    if cursor[1] == len(current_line) - 1:
        if cursor[0] != len(content) - 1:
            content = [*previous_content, inline_previous_content + content[cursor[0] + 1], *content[cursor[0] + 2:]]
    else:
        content = [*previous_content, inline_previous_content + inline_next_content, *next_content]
    return content, cursor


def my_exit(*args):
    os.system('cls')
    exit(0)


def save(content, cursor):
    global show_save_menu
    if modified:
        show_save_menu = True
        return content, cursor
    else:
        my_exit()


def handle_control_characters(content, cursor):

    control_character_func_dict = {
        b'K': cursor_left,
        b'M': cursor_right,
        b'H': cursor_up,
        b'P': cursor_down,
        b'G': cursor_to_start,
        b'O': cursor_to_end,
        b'S': delete,
    }

    key = getch()
    if key in control_character_func_dict:
        return control_character_func_dict[key](content, cursor)


def handle_backspace(content, cursor):
    global modified
    modified = True
    if cursor[1] == 0:
        if cursor[0] != 0:
            tmp = len(content[cursor[0] - 1]) - 1
            content = [*content[:cursor[0] - 1], content[cursor[0] - 1][:-1] + current_line, *next_content]
            cursor[0] = max(0, cursor[0] - 1)
            cursor[1] = tmp
    else:
        content = [*previous_content, inline_previous_content[:-1] + current_char + inline_next_content, *next_content]
        cursor[1] -= 1
    return content, cursor


def handle_enter(content, cursor):
    global modified
    modified = True
    content = [*previous_content, inline_previous_content + '\n', current_char + inline_next_content, *next_content]
    cursor[0] += 1
    cursor[1] = 0
    return content, cursor


def handle_tabulator(content, cursor):
    global modified
    modified = True
    content = [*previous_content, inline_previous_content + '\t' + current_char + inline_next_content, *next_content]
    cursor[1] += 1
    return content, cursor


def handle_printable_character(content, cursor):
    global modified
    modified = True
    content = [*previous_content, inline_previous_content + key.decode('utf-8') + current_char + inline_next_content, *next_content]
    cursor[1] += 1
    return content, cursor


func_dict = {
    b'\x03': my_exit,  # C-c
    b'\x08': handle_backspace,  # backspace
    b'\x09': handle_tabulator,  # tabulator
    b'\x0d': handle_enter,  # enter
    b'\x18': save,  # C-x
    b'\xe0': handle_control_characters,
    **{chr(c).encode(encoding): handle_printable_character
       for c in range(32, 127)}  # printable characters
}

if __name__ == '__main__':
    if len(sys.argv) == 2:
        target_path = sys.argv[1]
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                print('This is a directory, not a file. Exiting.')
                exit(1)
            elif os.path.isfile(target_path):
                with open(target_path, 'r') as f:
                    content = f.readlines() or ['']
                    if content[-1][-1] == '\n':
                        content.append('\x00')
                    else:
                        content[-1] += '\x00'
                    show_screen(content)
        else:
            if is_path_exists_or_creatable_portable(target_path):
                open(target_path, 'w').close()  # TODO
                content = ['\x00']
                show_screen(content)
            else:
                print('This path is invalid.')
                exit(1)
    else:
        print('Usage: python3 pynano.py <file>')
        exit(1)

    while True:
        key = getch()
        current_line = content[cursor[0]]
        previous_content = content[:cursor[0]]
        next_content = content[cursor[0] + 1:]
        inline_previous_content = current_line[:cursor[1]]
        inline_next_content = current_line[cursor[1] + 1:]
        current_char = current_line[cursor[1]]

        if key in func_dict:
            content, cursor = func_dict[key](content, cursor)

        show_screen(content)
