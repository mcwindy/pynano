import os
import sys
from msvcrt import getch

debug = False
tab_equivalent_length = 4

cursor = [0, 0]
modified = False
show_save_menu = False
terminal_size = os.get_terminal_size()


def save_file(filename, content):
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
                print('\033[4;30;47m{}\033[0m{}'.format(*((' \n', '') if char == '\n' else (' ', ' ' * (tab_equivalent_length - 1)) if char == '\t' else (char,
                                                                                                                                                          ''))),
                      end='')
            else:
                print(' ' * tab_equivalent_length if char == '\t' else char, end='')
    print('~\n' * (terminal_size.lines - len(content) - 6 - debug * (1 + len(content))))

    # print(terminal_size.lines - len(content) - 2 * int(show_save_menu) - 4)
    if show_save_menu:
        print('Save change? (Y/N) | C-c to cancel')
        while True:
            key = getch()
            if key == b'\x03':
                show_save_menu = False
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


def my_exit():
    os.system('cls')
    exit(0)


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


if __name__ == '__main__':
    if len(sys.argv) == 2:
        target_path = sys.argv[1]
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                print('This is a directory, not a file. Exiting.')
                exit(1)
            elif os.path.isfile(target_path):
                with open(target_path, 'r') as f:
                    content = f.readlines()
                    # content = [line + '\n' for line in content]
                    show_screen(content)
        else:
            if is_path_exists_or_creatable_portable(target_path):
                open(target_path, 'w').close()  # TODO
                content = ['']
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
        if key == b'\x03':  # C-c
            my_exit()
        elif key == b'\xe0':
            key = getch()

            if key == b'K':
                if cursor[1] == 0:
                    if cursor[0] != 0:
                        cursor[0] = max(0, cursor[0] - 1)
                        cursor[1] = len(content[cursor[0]]) - 1
                else:
                    cursor[1] -= 1
            elif key == b'M':
                if cursor[1] == len(current_line) - 1:
                    if cursor[0] != len(content) - 1:
                        cursor[0] = min(len(content) - 1, cursor[0] + 1)
                        cursor[1] = 0
                else:
                    cursor[1] += 1
            elif key == b'H':
                cursor[0] = max(0, cursor[0] - 1)
                cursor[1] = min(len(content[cursor[0]]) - 1, cursor[1])
            elif key == b'P':
                cursor[0] = min(len(content) - 1, cursor[0] + 1)
                cursor[1] = min(len(content[cursor[0]]) - 1, cursor[1])
            elif key == b'S':  # delete
                modified = True
                if cursor[1] == len(current_line) - 1:
                    if cursor[0] != len(content) - 1:
                        content = [*previous_content, inline_previous_content + content[cursor[0] + 1], *content[cursor[0] + 2:]]
                else:
                    content = [*previous_content, inline_previous_content + inline_next_content, *next_content]
            elif key == b'G':  # home
                cursor[1] = 0
            elif key == b'O':  # end
                cursor[1] = len(current_line) - 1
        elif key == b'\x18':  # C-x save
            if modified:
                show_save_menu = True
            else:
                my_exit()
        elif key == b'\x08':  # backspace
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
        elif key == b'\r':  # enter
            modified = True
            content = [*previous_content, inline_previous_content + '\n', current_char + inline_next_content, *next_content]
            cursor[0] += 1
            cursor[1] = 0
        elif key == b'\t':  # tabulator
            modified = True
            content = [*previous_content, inline_previous_content + '\t' + current_char + inline_next_content, *next_content]
            cursor[1] += 1
        elif 32 <= ord(key) <= 126:  # printable characters
            modified = True
            content = [*previous_content, inline_previous_content + key.decode('utf-8') + current_char + inline_next_content, *next_content]
            cursor[1] += 1
        show_screen(content)
