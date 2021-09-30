#!/usr/bin/env python3

import pexpect
import pprint
import re
from distutils.spawn import find_executable
from collections import OrderedDict

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

    # m = re.search(r'(?P<prepromt_r>\r\n|\n\r)(?P<prepromt_keys>.*)'+prompt+r'(?P<echo>{})?(?P<postcmd_keys>.*)(?P<cmd_ret>\r\n|\n\r)'.format(tclputs(end)), substr, re.DOTALL)
    labels = ['prevcmd_end','prepromt_keys','echo','postcmd_keys','cmd_ack']
    m = re.search(r'(\r\n|\n\r)(.*)'+prompt+r'({})?(.*)(\r\n|\n\r)'.format(tclputs(end)), substr, re.DOTALL)
    if not m:
        print('WARNING: No match found')
        return

    groupdict = OrderedDict(zip(labels, m.groups()))
    for k,v in groupdict.items():
        print('-', k+":", repr(v))
    print()


def test_tclconsole(cmd, args, prompt):
    if not find_executable(cmd):
        print('Command', cmd, 'not found. Skipping.')
    vh = pexpect.spawn(cmd, args, echo=True, timeout=10, encoding='utf-8')
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
    print(repr(vh.before)+'\n')

    analyze(vh.before, mrk_start, mrk_end, prompt)


# Go----

# print('- Vivado -'+'-'*40)
# test_tclconsole('vivado',['-mode','tcl'], u'Vivado%\s')

# print('- Questa -'+'-'*40)
# test_tclconsole('vsim',['-c'], u'QuestaSim>\s\rQuestaSim>\s')

# print('- Vivado HLS -'+'-'*40)
# test_tclconsole('vitis_hls', ['-i'], u'vitis_hls>\s')

print('- Vivado HLS -'+'-'*40)
test_tclconsole('vivado_hls', ['-i'], u'vivado_hls>\s')