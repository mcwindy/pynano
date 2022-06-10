import os
import sys
from msvcrt import getch

debug = False
tab_equivalent_length = 4

cursor = [0, 0]
modified = False
show_save_menu = False
show_search_menu = False
terminal_size = os.get_terminal_size()
encoding = 'utf-8'
search_word = ''
search_status = 0
history = []


def record_history(func):  # TODO[enhancemnet] record which operation and changes to save space

    def wrapper(content, cursor):
        global history
        history.append((content[:], cursor[:]))
        return func(content, cursor)

    return wrapper


def save_file(filename, content):
    content[-1] = content[-1][:-1]  # remove EOF symbol
    with open(filename, 'w') as f:
        f.write(''.join(content))


def show_screen(content):
    global show_save_menu, show_search_menu, cursor
    os.system('cls')
    print('\tpynano v0.1')
    print('-' * terminal_size.columns, end='')
    for i, line in enumerate(content):
        for j, char in enumerate(line):
            if [i, j] == cursor:
                print('\033[4;30;47m{}\033[0m{}'.format(
                    *((' \n', '') if char == '\n' else (' ', ' ' * (tab_equivalent_length - 1)) if char == '\t' else (' ', '') if char == '\x00' else (char,
                                                                                                                                                       ''))),
                      end='')  # highlight bug
            else:
                print(' ' * tab_equivalent_length if char == '\t' else ' ' if char == '\x00' else char, end='')
    print('\n~' * (terminal_size.lines - len(content) - 6 - debug * (1 + len(content))))

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
                filename = get_filename()
                save_file(filename, content)
                my_exit()
            elif key == b'N' or key == b'n':
                # TODO[enhancement] save file to tmp
                my_exit()
    elif show_search_menu:
        global search_word
        print('Word to search: ' + search_word)
        print('C-c to cancel')
        if search_status == 1:
            print('Found')
        elif search_status == 2:
            print('Start search from begining, not found')
        elif search_status == 3:
            print('Start search from end, found')

    else:
        print('C-x to save | C-c to exit')
    if debug:
        print(cursor)
        print(content)
        print(history)


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


@record_history
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


def error_exit(statement):
    # os.system('cls')
    print(statement)
    exit(1)


def save(content, cursor):
    global show_save_menu
    if modified:
        show_save_menu = True
        return content, cursor
    else:
        my_exit()


def undo(content, cursor):
    global history
    if len(history) != 0:
        return history.pop()
    else:
        return content, cursor


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


@record_history
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


@record_history
def handle_enter(content, cursor):
    global modified
    modified = True
    content = [*previous_content, inline_previous_content + '\n', current_char + inline_next_content, *next_content]
    cursor[0] += 1
    cursor[1] = 0
    return content, cursor


def handle_search(content, cursor):
    global show_search_menu
    show_search_menu = True
    return content, cursor


@record_history
def handle_tabulator(content, cursor):
    global modified
    modified = True
    content = [*previous_content, inline_previous_content + '\t' + current_char + inline_next_content, *next_content]
    cursor[1] += 1
    return content, cursor


@record_history
def handle_printable_character(content, cursor):
    global modified
    modified = True
    content = [*previous_content, inline_previous_content + key.decode('utf-8') + current_char + inline_next_content, *next_content]
    cursor[1] += 1
    return content, cursor


def search(content, cursor, word):
    global search_status
    search_status = 1  # 1: found 2:from beginning
    if word in inline_next_content:
        cursor[1] += inline_next_content.index(word) + 1
    else:
        search_status |= 2
        for i in range(cursor[0] + 1, len(content)):
            if word in content[i]:
                cursor[0] = i
                cursor[1] = content[i].index(word)
                break
        else:
            for i in range(0, cursor[0]):
                if word in content[i]:
                    cursor[0] = i
                    cursor[1] = content[i].index(word)
                    break
            else:
                if word in current_line:
                    cursor[1] = current_line.index(word)
                else:
                    search_status ^= 1
                    print('word not found')


def search_menu():
    global show_search_menu
    if key == b'\x03':
        show_search_menu = False
    elif key == b'\x08':
        search_word = search_word[:-1]
    elif key == b'\x0d':
        search(content, cursor, search_word)
        show_search_menu = False
    elif 32 <= ord(key) < 127:
        search_word += key.decode('utf-8')
        print("search_word:", search_word)


def load_file():
    if len(sys.argv) == 2:
        target_path = sys.argv[1]
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                # TODO[enhancement] choose file
                error_exit('This is a directory, not a file. Exiting.')
            elif os.path.isfile(target_path):
                with open(target_path, 'r') as f:
                    content = f.readlines()
                    if content:
                        content[-1] += '\x00'
                    else:
                        content.append('\x00')

                    show_screen(content)
                return target_path, content
        else:
            open(target_path, 'w').close()
            content = ['\x00']
            show_screen(content)
            return target_path, content
    else:
        error_exit('Usage: python3 pynano.py <file>')


func_dict = {
    b'\x03': my_exit,  # C-c
    b'\x08': handle_backspace,  # backspace
    b'\x09': handle_tabulator,  # tabulator
    b'\x0d': handle_enter,  # enter
    b'\x17': handle_search,  # C-w
    b'\x18': save,  # C-x
    b'\x1a': undo,
    b'\xe0': handle_control_characters,
    **{chr(c).encode(encoding): handle_printable_character
       for c in range(32, 127)}  # printable characters
}

# TODO copy paste cut shift-select
if __name__ == '__main__':
    target_path, content = load_file()

    while True:
        show_screen(content)
        key = getch()
        current_line = content[cursor[0]]
        previous_content = content[:cursor[0]]
        next_content = content[cursor[0] + 1:]
        inline_previous_content = current_line[:cursor[1]]
        inline_next_content = current_line[cursor[1] + 1:]
        current_char = current_line[cursor[1]]

        if show_search_menu:
            search_menu(key)
        else:
            if key in func_dict:
                content, cursor = func_dict[key](content, cursor)
