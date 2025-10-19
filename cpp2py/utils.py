# cpp2py/utils.py
def indent_text(s: str, indent_level: int = 0):
    prefix = ' ' * (4 * indent_level)
    return '\n'.join(prefix + line if line.strip() != '' else line for line in s.split('\n'))
