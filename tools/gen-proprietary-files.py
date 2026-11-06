#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
"""Generate a proprietary-files.txt draft from a stock RTD1325 dump.

Walks vendor/ (and odm/) of an unpacked OTA, drops everything LineageOS builds
from source or that this tree carries itself, sorts the rest into sections and
writes a list extract-utils understands. The result is a *draft*: review it,
move board specific bits to the device tree's own list, and keep the
hand-made edits in the curated proprietary-files.txt.

What gets dropped:

  * toybox/toolbox applet symlinks in vendor/bin and other symlinks
  * partition metadata: build.prop, fs_config_*, selinux/, vintf manifest and
    compatibility matrix, linker.config.pb, NOTICE, group/passwd
  * files the common tree installs from source (fstab, ueventd, init.rtd1325*,
    init.insmod.cfg, ...) -- see TREE_FILES
  * HALs LineageOS builds from source -- see SOURCE_BUILT
  * stable AIDL/HIDL interface libraries (android.hardware.* & co) that exist
    as Soong modules, so that the blobs link the source built ones and Soong
    does not see two modules installing the same file
  * config files byte-identical to a copy in frameworks/ (permissions,
    AOSP audio policy files): those get installed from source

Then every kept ELF's DT_NEEDED is resolved against the kept blobs, LLNDK and
the module index; anything that resolves to nothing is reported, because the
Python extract-utils makes that a build error (check_elf_files).

Usage:
    gen-proprietary-files.py <dump> [-o proprietary-files.txt]
                             [--module-info out/target/product/X/module-info.json]
                             [--top <android top>] [--sha1]
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

PARTITIONS = ('vendor', 'odm')

# Metadata that is generated at build time.
GENERATED = [
    r'^(vendor|odm)/build\.prop$',
    r'^(vendor|odm)/etc/build\.prop$',
    r'^(vendor|odm)/etc/fs_config_(dirs|files)$',
    r'^(vendor|odm)/etc/(group|passwd)$',
    r'^(vendor|odm)/etc/NOTICE\.xml\.gz$',
    r'^(vendor|odm)/etc/selinux/',
    r'^(vendor|odm)/etc/linker\.config\.pb$',
    r'^vendor/etc/vintf/manifest\.xml$',
    r'^vendor/etc/vintf/compatibility_matrix\.xml$',
    r'^vendor/etc/mkshrc$',
    r'^vendor/lib(64)?/modules/',
    r'^vendor/ta_inactive/dummy\.file$',
    r'^vendor/odm$',
]

# Installed by device/realtek/rtd1325-common from source.
TREE_FILES = [
    r'^vendor/etc/audio_policy_configuration\.xml$',
    # Retain /vendor/ta through the source-installed empty mount-point marker.
    r'^vendor/ta/dummy\.file$',
    r'^vendor/etc/fstab\.rtd1325$',
    r'^vendor/etc/fstab\.zram\.',
    r'^vendor/etc/ueventd\.rc$',
    r'^vendor/etc/init\.insmod\.cfg$',
    r'^vendor/etc/init/init\.rtd1325(\..*)?\.rc$',
    r'^vendor/etc/init/init\.common\.usb\.rc$',
    r'^vendor/etc/init/vndservicemanager\.rc$',
    # stock HALs renamed to .rtk (AOSP modules of the same name), their rc
    # files live in the tree
    r'^vendor/etc/init/android\.hardware\.(wifi-service|audio\.service|bluetooth@1\.1-service)\.rc$',
    r'^vendor/etc/init/boringssl_self_test\.rc$',
    r'^vendor/etc/wifi/wpa_supplicant\.conf$',
    r'^vendor/etc/wifi/(p2p_supplicant|wpa_supplicant)_overlay\.conf$',
    r'^vendor/etc/permissions/android\.software\.xml$',
    r'^vendor/fonts/',
]

# Built from source by LineageOS, together with their rc/vintf fragments.
SOURCE_BUILT = [
    r'^vendor/bin/(toybox_vendor|toolbox|sh|vndservicemanager|logwrapper)$',
    r'^vendor/bin/boringssl_self_test(32|64)$',
    r'^vendor/bin/hw/(hostapd|wpa_supplicant)$',
    r'^vendor/bin/hostapd_cli$',
    r'^vendor/etc/init/(hostapd\.android|android\.hardware\.wifi\.supplicant-service)\.rc$',
    r'^vendor/etc/vintf/manifest/android\.hardware\.wifi\.(hostapd|supplicant)\.xml$',
    r'^vendor/lib(64)?/libwpa_client\.so$',
    r'^vendor/bin/hw/android\.hardware\.boot-service\.default$',
    r'^vendor/etc/init/android\.hardware\.boot-service\.default\.rc$',
    r'^vendor/etc/vintf/manifest/android\.hardware\.boot-service\.default\.xml$',
    r'^vendor/bin/hw/android\.hardware\.health-service\.example$',
    r'^vendor/etc/init/android\.hardware\.health-service\.example\.rc$',
    r'^vendor/etc/vintf/manifest/android\.hardware\.health-service\.example\.xml$',
    r'^vendor/bin/hw/android\.hardware\.drm-service\.clearkey$',
    r'^vendor/etc/init/android\.hardware\.drm-service\.clearkey\.rc$',
    r'^vendor/etc/vintf/manifest/android\.hardware\.drm-service\.clearkey\.xml$',
    r'^vendor/bin/hw/android\.hardware\.cas-service\.example$',
    r'^vendor/etc/init/cas-default\.rc$',
    r'^vendor/etc/vintf/manifest/android\.hardware\.cas-service\.xml$',
    r'^vendor/lib(64)?/hw/local_time\.default\.so$',
    r'^vendor/lib(64)?/android\.hardware\.bluetooth\.audio-impl\.so$',
    r'^vendor/lib(64)?/libbluetooth_audio_session(_aidl)?\.so$',
    r'^vendor/lib(64)?/hw/audio\.bluetooth\.default\.so$',
    r'^vendor/lib(64)?/hw/android\.hardware\.bluetooth\.audio@2\.1-impl\.so$',
    r'^vendor/etc/vintf/manifest/bluetooth_audio\.xml$',
    r'^vendor/etc/seccomp_policy/(mediacodec|mediaswcodec)\.policy$',
    r'^vendor/bin/(awk|dumpsys|vndservice|gpu_counter_producer)$',
    r'^vendor/lib(64)?/libbinderdebug\.so$',
    # only the stock wpa_supplicant links it
    r'^vendor/lib(64)?/libkeystore-engine-wifi-hidl\.so$',
    # clearkey CAS and its private protobuf
    r'^vendor/lib(64)?/mediacas/libclearkeycasplugin\.so$',
    r'^vendor/lib(64)?/libprotobuf-cpp-(full|lite)-21\.7\.so$',
    # no modem, and nothing links them
    r'^vendor/lib(64)?/lib(reference-ril|ril|rilutils)\.so$',
    # software OMX: media_codecs.xml declares no OMX.google.* codec
    r'^vendor/lib(64)?/libstagefright_(soft_[a-z0-9]+|softomx|softomx_plugin)\.so$',
    # C libraries, stubs and codecs with a stable ABI that Android 16 builds
    # for vendor itself (vendor_available); a stock copy would clash with it
    r'^vendor/lib(64)?/lib(opus|vpx|vorbisidec|drm|trusty|hwbinder|hidltransport|memunreachable|avservices_minijail|vibratorutils)\.so$',
    r'^vendor/lib(64)?/libstagefright_(flacdec|amrnb_common|enc_common)\.so$',
    # haptics on a TV box; not in audio_effects.xml, and its libvibratorutils
    # is not visible to vendor prebuilts
    r'^vendor/lib(64)?/soundfx/libhapticgenerator\.so$',
]

# Interface libraries: drop them when a Soong module of that name exists.
INTERFACE_LIB = re.compile(
    r'^(android\.(hardware|hidl|system|frameworks)\..+|'
    r'android\.media\.audio\.common\.types-V\d+-(ndk|cpp))\.so$')

# Provided to vendor by the platform.
LLNDK = {
    'libEGL.so', 'libGLESv1_CM.so', 'libGLESv2.so', 'libGLESv3.so',
    'libandroid_net.so', 'libbinder_ndk.so', 'libc.so', 'libcgrouprc.so',
    'libdl.so', 'libft2.so', 'liblog.so', 'libm.so', 'libmediandk.so',
    'libnativewindow.so', 'libneuralnetworks.so', 'libselinux.so',
    'libsync.so', 'libvndksupport.so', 'libvulkan.so', 'libRS.so',
    'libstatssocket.so', 'libapexsupport.so', 'libaconfig_storage_read_api_cc.so',
    'libbinder_rpc_unstable.so', 'libcom.android.tethering.connectivity_native.so',
    'ld-android.so', 'libstdc++.so',
}

# Section assignment, first match wins.
SECTIONS = [
    ('ATV', r'(RtkAFWLC|RtkKeyset|KeysetSample|libRtkKeyset|/overlay/|tv_input|PQ_ctrl|libsideband|SidebandClient|sideband|rtk_media_sideband)'),
    ('Audio', r'(audio|soundfx|libtinyalsa|libtinycompress|alsa|mixer_paths|libeffects|libnbaio|karaoke|HDMIRxAudio|surround_sound|sco_audio|libvibratorutils)'),
    ('Bluetooth', r'(bluetooth|libbt-|/firmware/rtl87|/firmware/rtl88|/firmware/rtl89|/firmware/rtl8761|skwbt|sv6160|SWT6621S)'),
    ('Camera', r'(camera|libjpu|libencjpgwrap|libdecjpgwrap)'),
    ('DRM', r'(drm|mediacas|libpraidl|liboemcrypto|playready|widevine|cas\b|libDrmExt|nrdp|ms12)'),
    ('Gatekeeper', r'gatekeeper'),
    ('Graphics', r'(graphics|gralloc|egl|mali|vulkan|hwc3|composer|libgui_rtk|libsync_rtk|librtk_ion|libext_rtk_ion|librtkion|libion|libRTKAllocator|libbuflock|rtk_sw_sync|gpu_counter|libhwse|hdcp|hdmi|HDMI|libVoutUtil|voututil|librtk_ion_util|renderscript|libsigchain_rtk|libdrm\.so)'),
    ('Input', r'/usr/(idc|keylayout)/'),
    ('Keymint', r'(keymint|keymaster|keystore|secureclock|sharedsecret|libsoft_attestation|libcppbor|libcppcose|rkp_factory|libpuresoftkeymaster)'),
    ('Media', r'(media|codec|c2|omx|OMX|stagefright|libvpu|libvpx|libopus|libvorbis|libDeInterlace|libdecve1|libwrapcommon|librtk_media|libRTKOMX|libRTK_lib|librtk_c2|libjpeg|seccomp_policy|libavservices|libmediautils|libtf|/tf/|libRtkIpc|libRpcMem|librtk_codec2)'),
    ('Power', r'(power|thermal|cpuset_control|ipa_controller)'),
    ('Radio', r'(rild?\b|libreference-ril|libril|librilutils|radio)'),
    ('SE util', r'seutil'),
    ('TEE', r'(tee|TEE|optee|\.ta$|/ta/|libtrusty|librtkotp|startTEESup)'),
    ('USB', r'usb'),
    ('Wi-Fi', r'(wifi|wpa|hostapd|dhcpcd|iprenew|wifi_auto_insmod|libkeystore-engine-wifi)'),
]


def is_elf(path):
    try:
        with open(path, 'rb') as f:
            return f.read(4) == b'\x7fELF'
    except OSError:
        return False


def needed(path):
    out = subprocess.run(['readelf', '-dW', path], capture_output=True,
                         env=dict(os.environ, LC_ALL='C'),
                         text=True).stdout
    return re.findall(r'\(NEEDED\)\s+Shared library: \[(.+?)\]', out)


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_modules(module_info):
    if not module_info:
        return None
    with open(module_info) as f:
        return set(json.load(f).keys())


def frameworks_hashes(top):
    """sha1 -> path for config files LineageOS can install from source."""
    hashes = {}
    if not top:
        return hashes
    for d in ('frameworks/native/data/etc',
              'frameworks/av/services/audiopolicy/config',
              'frameworks/av/media/libeffects/data',
              'frameworks/av/media/libstagefright/data'):
        root = os.path.join(top, d)
        for dirpath, _, files in os.walk(root):
            for name in files:
                if name.endswith('.xml'):
                    p = os.path.join(dirpath, name)
                    hashes.setdefault(sha1(p), os.path.relpath(p, top))
    return hashes


def section_of(path):
    for name, pattern in SECTIONS:
        if re.search(pattern, path):
            return name
    return 'Misc'


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('dump')
    parser.add_argument('-o', '--output', default='-')
    parser.add_argument('--module-info',
                        help='module-info.json of any earlier build, used to '
                        'decide which libraries LineageOS can build')
    parser.add_argument('--top', default=os.environ.get('ANDROID_BUILD_TOP'),
                        help='Android tree, to detect configs identical to '
                        'their frameworks/ copy')
    parser.add_argument('--sha1', action='store_true',
                        help='pin every entry to its sha1')
    parser.add_argument('--source', default='',
                        help='text for the "All blobs are from" header')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='list every dropped file')
    args = parser.parse_args()

    dump = os.path.abspath(args.dump)
    modules = load_modules(args.module_info)
    fw_hashes = frameworks_hashes(args.top)
    skip = [re.compile(p) for p in GENERATED + TREE_FILES + SOURCE_BUILT]

    kept = []
    dropped = defaultdict(list)
    for part in PARTITIONS:
        root = os.path.join(dump, part)
        for dirpath, dirnames, files in os.walk(root):
            dirnames.sort()
            for name in sorted(files):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, dump)
                if os.path.islink(full):
                    dropped['symlink'].append(rel)
                    continue
                if any(p.search(rel) for p in skip):
                    dropped['tree/source'].append(rel)
                    continue
                if (INTERFACE_LIB.match(name) and '-impl' not in name
                        and re.match(r'^(vendor|odm)/lib(64)?/[^/]+$', rel)
                        and modules is not None and name[:-3] in modules):
                    dropped['interface lib (source)'].append(rel)
                    continue
                if fw_hashes and not is_elf(full) and name.endswith('.xml'):
                    match = fw_hashes.get(sha1(full))
                    if match:
                        dropped['identical to frameworks'].append(
                            f'{rel} = {match}')
                        continue
                kept.append(rel)

    # Resolve DT_NEEDED of what is kept
    provided = defaultdict(set)  # libdir -> names
    for rel in kept:
        m = re.match(r'^(vendor|odm)/(lib(64)?)/(.+)$', rel)
        if m and rel.endswith('.so'):
            provided[m.group(2)].add(os.path.basename(rel))
    unresolved = defaultdict(set)
    from_source = defaultdict(set)
    for rel in kept:
        full = os.path.join(dump, rel)
        if not is_elf(full):
            continue
        libdir = 'lib64' if '/lib64/' in rel or (
            '/bin/' in rel and 'aarch64' in subprocess.run(
                ['file', '-b', full], capture_output=True, text=True).stdout
        ) else 'lib'
        for lib in needed(full):
            if lib in LLNDK or lib in provided[libdir]:
                continue
            if modules is not None and lib[:-3] in modules:
                from_source[lib].add(rel)
                continue
            unresolved[lib].add(rel)

    by_section = defaultdict(list)
    for rel in kept:
        by_section[section_of(rel)].append(rel)

    out = sys.stdout if args.output == '-' else open(args.output, 'w')
    header = args.source or os.path.basename(dump)
    print(f'## All blobs are from {header}, unless pinned and noted as otherwise.',
          file=out)
    print('## Generated by tools/gen-proprietary-files.py, then edited by hand.',
          file=out)
    for name in sorted(by_section):
        print(f'\n## {name}', file=out)
        for rel in sorted(by_section[name], key=str.lower):
            entry = rel
            if args.sha1:
                entry += '|' + sha1(os.path.join(dump, rel))
            print(entry, file=out)
    if out is not sys.stdout:
        out.close()

    print(f'kept {len(kept)} files', file=sys.stderr)
    for reason, files in sorted(dropped.items()):
        print(f'dropped {len(files):4d} ({reason})', file=sys.stderr)
        if args.verbose and reason != 'symlink':
            for f in files:
                print(f'    {f}', file=sys.stderr)
    if modules is None:
        print('\nNo --module-info given: interface libraries were kept and '
              'DT_NEEDED was resolved against the blobs only.', file=sys.stderr)
    if from_source:
        print('\nLibraries the blobs will link from source:', file=sys.stderr)
        for lib in sorted(from_source):
            print(f'  {lib}', file=sys.stderr)
    if unresolved:
        print('\nUNRESOLVED (neither a kept blob, LLNDK nor a Soong module):',
              file=sys.stderr)
        for lib in sorted(unresolved):
            users = sorted(unresolved[lib])
            more = f' (+{len(users) - 3})' if len(users) > 3 else ''
            print(f'  {lib}: {", ".join(users[:3])}{more}', file=sys.stderr)


if __name__ == '__main__':
    main()
