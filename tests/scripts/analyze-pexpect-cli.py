#!/usr/bin/python
from __future__ import print_function, absolute_import
from builtins import range
import six

import pexpect
from distutils.spawn import find_executable
import re

def tclputs(word):
    return 'puts "{}"'.format(word)

def analyze(string, start, end, prompt):
    
    print("|- Analysing -|")
    # print(string.count(start))
    # print(string.count(end))
    echoStart = string.find(tclputs(start)) != -1
    echoEnd = string.find(tclputs(end)) != -1
    if echoStart != echoEnd:
        print("WARNING: only one between the start or end marker were echoed")
    echoOn = echoStart

    pattern = r'[^"]{}(.*){}[^"]'.format(start, end)
    substr = re.search(pattern, string, re.DOTALL).group(1)

    print(repr(substr))
    print(repr(re.search(r'(.*)'+prompt+r'({})?(.*)'.format(tclputs(end)), substr, re.DOTALL).groups()))


def test_tclconsole(cmd, args, prompt):
    if not find_executable(cmd):
        print('Command', cmd, 'not found. Skipping.')
    vh = pexpect.spawn(cmd, args, echo=True, timeout=10)
    vh.expect(prompt)
    print('-- banner --')
    print (repr(vh.before)+'\n')


    mrk_start = 'AUG'
    mrk_end = 'GUA'

    vh.send(tclputs(mrk_start)+'\n')
    vh.send(tclputs(mrk_end)+'\n')
    vh.send(tclputs('AAA')+';'+tclputs('BBB')+';'+tclputs('CCC\\n')+'\n')
    vh.send('quit\n')

    o = vh.expect(pexpect.EOF)
    print('-- body --')
    print(repr(vh.before)+'\n')

    print('-- output -- ')
    print(vh.before+'\n')

    analyze(vh.before, mrk_start, mrk_end, prompt)


# Go----
print('- Vivado HLS -'+'-'*40)
test_tclconsole('vivado_hls', ['-i'], u'vivado_hls>\s')

print('- Vivado -'+'-'*40)
test_tclconsole('vivado',['-mode','tcl'], u'Vivado%\s')

print('- Questa -'+'-'*40)
test_tclconsole('vsim',['-c'], u'QuestaSim>\s\rQuestaSim>\s')