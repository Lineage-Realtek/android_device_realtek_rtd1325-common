#!/bin/bash
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
# Import the stock GKI kernel, device trees and kernel modules of an RTD1325
# box into a prebuilt kernel directory (e.g. device/realtek/rtx2-kernel).
#
# The dump must be an unpacked OTA, as produced by e.g. dumpyara:
#   boot/kernel                       gzip'ed arm64 Image
#   vendor_boot/dtb.img               the board dtb
#   dtbo.img                          the stock dtbo image
#   vendor_boot/ramdisk/lib/modules   first stage modules
#   vendor_dlkm/lib/modules           vendor modules
#   system_dlkm/lib/modules           GKI modules (signed, keep them as-is)
#
# Usage: import-prebuilt-kernel.sh <dump dir> <prebuilt kernel dir>

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <dump dir> <prebuilt kernel dir>"
    exit 1
fi

DUMP=$(realpath "$1")
OUT=$(realpath -m "$2")

for f in boot/kernel vendor_boot/dtb.img dtbo.img \
        vendor_boot/ramdisk/lib/modules/modules.load \
        vendor_dlkm/lib/modules/modules.load \
        system_dlkm/lib/modules/modules.dep; do
    if [ ! -e "$DUMP/$f" ]; then
        echo "Missing $DUMP/$f"
        exit 1
    fi
done

rm -rf "$OUT/modules" "$OUT/dtb"
mkdir -p "$OUT/dtb" "$OUT/modules/vendor_boot" "$OUT/modules/vendor_dlkm" "$OUT/modules/system_dlkm"

# Kernel: boot.img v4 holds an Image.gz
cp "$DUMP/boot/kernel" "$OUT/Image.gz"

# DTB goes into vendor_boot, BOARD_PREBUILT_DTBIMAGE_DIR wants *.dtb
cp "$DUMP/vendor_boot/dtb.img" "$OUT/dtb/rtd1325.dtb"
cp "$DUMP/dtbo.img" "$OUT/dtbo.img"

# Modules
cp "$DUMP"/vendor_boot/ramdisk/lib/modules/*.ko "$OUT/modules/vendor_boot/"
cp "$DUMP"/vendor_dlkm/lib/modules/*.ko "$OUT/modules/vendor_dlkm/"
cp "$DUMP"/system_dlkm/lib/modules/*.ko "$OUT/modules/system_dlkm/"

# Load lists. Stock vendor_dlkm modules.load is only what init.insmod.cfg
# expects to find, the real load order lives in init.insmod.cfg.
cp "$DUMP/vendor_boot/ramdisk/lib/modules/modules.load" "$OUT/modules/vendor_boot.modules.load"
cp "$DUMP/vendor_dlkm/lib/modules/modules.load" "$OUT/modules/vendor_dlkm.modules.load"
if [ -s "$DUMP/system_dlkm/lib/modules/modules.load" ]; then
    cp "$DUMP/system_dlkm/lib/modules/modules.load" "$OUT/modules/system_dlkm.modules.load"
else
    : > "$OUT/modules/system_dlkm.modules.load"
fi

# Modules found in the dump but not listed in any modules.load
for part in vendor_boot vendor_dlkm; do
    comm -23 <(ls "$OUT/modules/$part" | sort) <(sort "$OUT/modules/$part.modules.load") \
        > "$OUT/modules/$part.modules.unlisted"
    [ -s "$OUT/modules/$part.modules.unlisted" ] || rm "$OUT/modules/$part.modules.unlisted"
done

KVER=$(zcat "$OUT/Image.gz" | strings | grep -m1 -oE 'Linux version [^ ]+' | cut -d' ' -f3)
echo "$KVER" > "$OUT/kernel_version"

echo "Imported kernel $KVER:"
echo "  vendor_boot: $(ls "$OUT/modules/vendor_boot" | wc -l) modules"
echo "  vendor_dlkm: $(ls "$OUT/modules/vendor_dlkm" | wc -l) modules"
echo "  system_dlkm: $(ls "$OUT/modules/system_dlkm" | wc -l) modules"
