kColorMap = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3,
    'blue': 4,
    'magenta': 5,
    'cyan': 6,
    'lightgray': 7,
    'orange': 215
}

for n, c in kColorMap.items():
    vars()['k' + n.capitalize()] = '\x1b[38;5;{}m'.format(c)

kReset = '\x1b[0m'
