#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
"""Keep the RENAMED / RENAMED_USERS tables of extract-files.py in sync.

A stock vendor library that has the name of a vendor_available AOSP module
fails Soong with "partition is different", or with "depends on multiple
versions of the same aidl_interface". When the processes using it are stock,
the fix is to ship it as <name>-rtk.so: proprietary-files.txt gets a
src:dst entry, the library its soname fixed and every blob linking it a
replace_needed(). This script does all of that for the given names, reading
DT_NEEDED from the dump.

Usage: update-renames.py <dump> [libname ...]
       (libname without .so; with no names it only refreshes the users)
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACT = os.path.join(HERE, 'extract-files.py')
LIST = os.path.join(HERE, 'proprietary-files.txt')


def needed(path):
    out = subprocess.run(['readelf', '-dW', path], capture_output=True,
                         text=True, env=dict(os.environ, LC_ALL='C')).stdout
    return re.findall(r'\(NEEDED\)\s+Shared library: \[(.+?)\]', out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dump = sys.argv[1]
    add = sys.argv[2:]

    s = open(EXTRACT).read()
    a = s.index('RENAMED = (\n')
    b = s.index(')\n', a)
    renamed = re.findall(r"    '([^']+)',", s[a:b])
    renamed += [x for x in add if x not in renamed]

    blobs = []
    out = []
    for line in open(LIST).read().splitlines():
        if line.startswith('vendor/'):
            src = line.split('|')[0].split(':')[0]
            blobs.append(src)
            m = re.match(r'vendor/lib/(.+)\.so$', src)
            if m and m.group(1) in renamed:
                line = f'{src}:vendor/lib/{m.group(1)}-rtk.so'
        out.append(line)
    open(LIST, 'w').write('\n'.join(out) + '\n')

    def dst(src):
        m = re.match(r'vendor/lib/(.+)\.so$', src)
        if m and m.group(1) in renamed:
            return f'vendor/lib/{m.group(1)}-rtk.so'
        return src

    deps = {}
    for src in blobs:
        full = os.path.join(dump, src)
        if os.path.isfile(full):
            with open(full, 'rb') as f:
                if f.read(4) == b'\x7fELF':
                    deps[src] = needed(full)

    block = 'RENAMED = (\n'
    block += ''.join(f"    '{r}',\n" for r in renamed)
    block += ')\n\nRENAMED_USERS = {\n'
    for r in renamed:
        users = sorted(dst(src) for src, n in deps.items() if f'{r}.so' in n)
        block += f"    '{r}': (\n"
        block += ''.join(f"        '{u}',\n" for u in users)
        block += '    ),\n'
    block += '}\n'

    c = s.index('RENAMED_USERS = {')
    d = s.index('\n}\n', c) + 3
    s = s[:a] + block + s[d:]

    # Blobs referenced by other fixup tables must use the renamed path too
    for r in renamed:
        s = re.sub(rf"(\n    )'vendor/lib/{re.escape(r)}\.so',",
                   rf"\1'vendor/lib/{r}-rtk.so',", s)
    open(EXTRACT, 'w').write(s)


if __name__ == '__main__':
    main()
