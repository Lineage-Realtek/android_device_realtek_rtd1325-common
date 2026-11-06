#!/usr/bin/env python3
"""Resolve every undefined symbol of every installed vendor/odm ELF.

This is the symbol-level counterpart to check-vendor-deps.py, which only checks
that each DT_NEEDED library exists. A library can be present and still be the
wrong build -- that is exactly what happens when a stock blob is paired with an
AOSP-built dependency across an AIDL version bump (e.g. shipping AOSP's
libbluetooth_audio_session_aidl.so, built against bluetooth.audio V4, next to
stock blobs compiled against V3). The failure mode is a runtime

    CANNOT LINK EXECUTABLE ...: cannot locate symbol "..." referenced by "..."

which no dependency-existence check can catch.

Resolution mirrors what the dynamic linker actually does: for each ELF, walk the
DT_NEEDED closure, union the defined dynamic symbols of everything in it, and
subtract. Only STB_GLOBAL undefined symbols are reported -- STB_WEAK ones are
legitimately allowed to stay unresolved (that is what weak means), and this tree
has a stable set of those from sanitiser and libc++ internals.

Like check-vendor-deps.py, the set of installed files comes from
obj/PACKAGING/<part>_intermediates/file_list.txt, NOT from the staging directory
and NOT from installed-files-*.json: build_image.py filters staging through
--input-directory-filter-file, so both of those overstate what really lands on
the partition.

Usage: check-vendor-symbols.py [OUT_DIR]
"""

import collections
import os
import subprocess
import sys

# Partitions whose ELFs we audit.
AUDIT = ("vendor", "odm")

# Partitions that may satisfy a dependency. Vendor code links against a handful
# of system libraries via the LLNDK allowlist, so system has to be searchable
# even though we never audit it here.
# Each entry maps a staging directory to the obj/PACKAGING intermediates that
# list what actually survives into the image.
#
# The system entry used to be "systemimage". Soong builds the filesystem images
# itself in Android 16 and writes obj/PACKAGING/system_intermediates, so the old
# name silently resolved to nothing and every system library read as "(missing
# library: liblog.so)" -- which the summary line counts as unresolved. If this
# tool ever reports hundreds of files with missing *libraries* rather than
# missing symbols, check these names against out/target/product/*/obj/PACKAGING
# first.
PROVIDERS = (
    ("vendor", "vendor"),
    ("odm", "odm"),
    ("vendor_dlkm", "vendor_dlkm"),
    ("system", "system"),
    ("system_ext", "system_ext"),
    ("product", "product"),
)

# Bionic and the linker come from an APEX whose contents are not enumerated in
# any file_list.txt, so they are indexed straight out of the staging tree.
APEX_LIB_DIRS = (
    "apex/com.android.runtime/lib/bionic",
    "apex/com.android.runtime/lib64/bionic",
)


def readelf(path, *args):
    try:
        return subprocess.run(
            ("readelf",) + args + ("-W", path),
            capture_output=True, text=True, check=False,
            env=dict(os.environ, LC_ALL="C"),
        ).stdout
    except OSError:
        return ""


def elf_class(path):
    """Return 32 or 64, or None if this is not an ELF we can read."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(5)
    except OSError:
        return None
    if head[:4] != b"\x7fELF":
        return None
    return {1: 32, 2: 64}.get(head[4])


def dyn_syms(path):
    """(defined, undefined_global) symbol name sets for one ELF.

    readelf's field layout is stable from the right but not from the left: the
    type column is localised (a Russian locale renders STT_GNU_IFUNC as
    "<специфичный для ОС>: 10", which contains spaces and shifts every
    subsequent column). LC_ALL=C above prevents that; parsing from the right
    keeps it robust anyway.
    """
    defined, undef = set(), set()
    for line in readelf(path, "--dyn-syms").splitlines():
        parts = line.split()
        if len(parts) < 8 or not parts[0].endswith(":"):
            continue
        name = parts[-1].split("@")[0]
        # Columns from the right: name, Ndx, Vis, Bind, Type.
        ndx = parts[-2]
        bind = parts[-4]
        if not name:
            continue
        if ndx == "UND":
            if bind == "GLOBAL":
                undef.add(name)
        else:
            defined.add(name)
    return defined, undef


def needed(path):
    out = []
    for line in readelf(path, "-d").splitlines():
        if "(NEEDED)" in line and "[" in line:
            out.append(line.split("[", 1)[1].split("]", 1)[0])
    return out


def installed(out_dir):
    """Map (basename, bitness) -> path for everything on the listed partitions."""
    index = {}
    audited = []
    for part, intermediates in PROVIDERS:
        listing = os.path.join(
            out_dir, "obj/PACKAGING",
            "%s_intermediates" % intermediates, "file_list.txt")
        if not os.path.exists(listing):
            continue
        with open(listing) as fh:
            for rel in fh:
                rel = rel.strip()
                if not rel or rel.endswith("/"):
                    continue
                full = os.path.join(out_dir, part, rel)
                if not os.path.isfile(full):
                    continue
                bits = elf_class(full)
                if bits is None:
                    continue
                index.setdefault((os.path.basename(full), bits), full)
                if part in AUDIT:
                    audited.append((("/%s/%s" % (part, rel)), full, bits))
    for rel in APEX_LIB_DIRS:
        d = os.path.join(out_dir, rel)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            full = os.path.join(d, name)
            if not os.path.isfile(full):
                continue
            bits = elf_class(full)
            if bits is not None:
                index.setdefault((name, bits), full)
    return index, audited


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("OUT")
    if not out_dir:
        sys.exit("usage: check-vendor-symbols.py OUT_DIR  (or set $OUT)")

    index, audited = installed(out_dir)
    cache = {}

    def syms_of(path):
        if path not in cache:
            cache[path] = dyn_syms(path)
        return cache[path]

    problems = collections.defaultdict(list)
    for label, path, bits in audited:
        _, undef = syms_of(path)
        if not undef:
            continue
        # DT_NEEDED closure, same-bitness only.
        seen, queue, provided = set(), list(needed(path)), set()
        missing_libs = []
        while queue:
            lib = queue.pop()
            if lib in seen:
                continue
            seen.add(lib)
            dep = index.get((lib, bits))
            if dep is None:
                missing_libs.append(lib)
                continue
            provided |= syms_of(dep)[0]
            queue.extend(needed(dep))
        for sym in sorted(undef - provided):
            problems[label].append(sym)
        for lib in missing_libs:
            problems[label].append("(missing library: %s)" % lib)

    for label in sorted(problems):
        print("%s:" % label)
        for item in problems[label]:
            print("    %s" % item)
    print("checked %d installed ELF files on %s, %d with unresolved symbols"
          % (len(audited), "/".join(AUDIT), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
