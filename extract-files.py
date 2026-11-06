#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)

from extract_utils.fixups_lib import (
    lib_fixups,
)

from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/realtek/rtd1325-common',
]

# Blobs the vendor-side libui of Android 14 is linked into. None of them is
# loaded into a framework process, so the Android 14 snapshot can be used
# without two libui copies meeting in one address space.
LIBUI_V34_USERS = (
    'vendor/bin/hw/android.hardware.graphics.composer3-service.rtk',
    'vendor/bin/sideband',
    'vendor/lib/camera.device.aidl-external-rtk-impl.so',
    'vendor/lib/libcodec2_hidl@1.0-rtk.so',
    'vendor/lib/libcodec2_hidl@1.1-rtk.so',
    'vendor/lib/libcodec2_hidl@1.2-rtk.so',
    'vendor/lib/libcodec2_vndk-rtk.so',
    'vendor/lib/libDeInterlace.so',
    'vendor/lib/libgui_rtk.so',
    'vendor/lib/librtk_c2_adec.so',
    'vendor/lib/librtk_c2_vdec.so',
    'vendor/lib/librtk_codec2_vendor_allocator.so',
    'vendor/lib/librtk_media_hw_rhal.so',
    'vendor/lib/librtk_media_hw_rpc.so',
    'vendor/lib/librtk_media_hw_ve1.so',
    'vendor/lib/librtk_media_sideband.so',
    'vendor/lib/libRTKAllocator.so',
    'vendor/lib/libRTKOMX_OSAL_RTK.so',
    'vendor/lib/libsideband.so',
    'vendor/lib/libstagefrighthw.so',
)

# Stock copies of libraries that Android 16 also builds for vendor
# (vendor_available). Two modules of one name are a Soong error ("partition is
# different"), and the processes using them -- audio, codec2, KeyMint -- are
# all stock, so these are installed as <name>-rtk.so (see
# proprietary-files.txt) instead of being swapped for the Android 16 build.
# Users listed by destination path, so a renamed user is listed renamed.
RENAMED = (
    'libalsautils',
    'libcodec2_vndk',
    'lib_android_keymaster_keymint_utils',
    'libcppbor_external',
    'libcppcose_rkp',
    'libkeymint',
    'libcodec2_hidl@1.0',
    'libcodec2_hidl@1.1',
    'libcodec2_hidl@1.2',
    'libstagefright_bufferpool@2.0.1',
    'libstagefright_aidl_bufferpool2',
    'libmediautils_vendor',
    'libeffectsconfig',
    'libkeymaster_messages',
    'libkeymaster_portable',
    'libpuresoftkeymasterdevice',
    'libsoft_attestation_cert',
    'libcodec2_hidl_plugin',
)

RENAMED_USERS = {
    'libalsautils': (
        'vendor/lib/hw/audio.usb.default.so',
    ),
    'libcodec2_vndk': (
        'vendor/bin/hw/android.hardware.media.c2@1.2-rtk-service',
        'vendor/lib/libc2plugin_store.so',
        'vendor/lib/libcodec2_hidl@1.0-rtk.so',
        'vendor/lib/libcodec2_hidl@1.1-rtk.so',
        'vendor/lib/libcodec2_hidl@1.2-rtk.so',
        'vendor/lib/libcodec2_hidl_plugin-rtk.so',
        'vendor/lib/librtk_c2_adec.so',
        'vendor/lib/librtk_c2_store.so',
        'vendor/lib/librtk_c2_vdec.so',
        'vendor/lib/librtk_codec2_vendor_allocator.so',
    ),
    'lib_android_keymaster_keymint_utils': (
        'vendor/lib/libkeymint-rtk.so',
        'vendor/lib/libkeymint_rtk.so',
    ),
    'libcppbor_external': (
        'vendor/bin/hw/android.hardware.security.keymint-service.rtk',
        'vendor/lib/libcppcose_rkp-rtk.so',
        'vendor/lib/libkeymaster_portable-rtk.so',
        'vendor/lib/libkeymint-rtk.so',
        'vendor/lib/libkeymint_rtk.so',
        'vendor/lib/libpuresoftkeymasterdevice-rtk.so',
    ),
    'libcppcose_rkp': (
        'vendor/lib/libkeymaster_portable-rtk.so',
        'vendor/lib/libpuresoftkeymasterdevice-rtk.so',
    ),
    'libkeymint': (
        'vendor/lib/libkeymint_rtk.so',
    ),
    'libcodec2_hidl@1.0': (
        'vendor/bin/hw/android.hardware.media.c2@1.2-rtk-service',
        'vendor/lib/libc2plugin_store.so',
        'vendor/lib/libcodec2_hidl@1.1-rtk.so',
        'vendor/lib/libcodec2_hidl@1.2-rtk.so',
        'vendor/lib/librtk_c2_adec.so',
        'vendor/lib/librtk_c2_store.so',
        'vendor/lib/librtk_c2_vdec.so',
        'vendor/lib/librtk_codec2_vendor_allocator.so',
    ),
    'libcodec2_hidl@1.1': (
        'vendor/bin/hw/android.hardware.media.c2@1.2-rtk-service',
        'vendor/lib/libc2plugin_store.so',
        'vendor/lib/libcodec2_hidl@1.2-rtk.so',
        'vendor/lib/librtk_c2_adec.so',
        'vendor/lib/librtk_c2_store.so',
        'vendor/lib/librtk_c2_vdec.so',
        'vendor/lib/librtk_codec2_vendor_allocator.so',
    ),
    'libcodec2_hidl@1.2': (
        'vendor/bin/hw/android.hardware.media.c2@1.2-rtk-service',
        'vendor/lib/libc2plugin_store.so',
        'vendor/lib/librtk_c2_adec.so',
        'vendor/lib/librtk_c2_store.so',
        'vendor/lib/librtk_c2_vdec.so',
        'vendor/lib/librtk_codec2_vendor_allocator.so',
    ),
    'libstagefright_bufferpool@2.0.1': (
        'vendor/lib/libcodec2_hidl@1.0-rtk.so',
        'vendor/lib/libcodec2_hidl@1.1-rtk.so',
        'vendor/lib/libcodec2_hidl@1.2-rtk.so',
        'vendor/lib/libcodec2_vndk-rtk.so',
        'vendor/lib/librtk_codec2_vendor_allocator.so',
    ),
    'libstagefright_aidl_bufferpool2': (
        'vendor/lib/libcodec2_vndk-rtk.so',
    ),
    'libmediautils_vendor': (
        'vendor/lib/hw/android.hardware.audio@7.0-impl.so',
    ),
    'libeffectsconfig': (
        'vendor/lib/libeffects.so',
    ),
    'libkeymaster_messages': (
        'vendor/lib/libkeymint-rtk.so',
        'vendor/lib/libkeymint_rtk.so',
        'vendor/lib/libpuresoftkeymasterdevice-rtk.so',
    ),
    'libkeymaster_portable': (
        'vendor/bin/hw/android.hardware.security.keymint-service.rtk',
        'vendor/lib/libkeymint-rtk.so',
        'vendor/lib/libkeymint_rtk.so',
        'vendor/lib/libpuresoftkeymasterdevice-rtk.so',
        'vendor/lib/libsoft_attestation_cert-rtk.so',
    ),
    'libpuresoftkeymasterdevice': (
        'vendor/lib/libkeymint-rtk.so',
    ),
    'libsoft_attestation_cert': (
        'vendor/lib/libpuresoftkeymasterdevice-rtk.so',
    ),
    'libcodec2_hidl_plugin': (
        'vendor/lib/libcodec2_hidl@1.0-rtk.so',
        'vendor/lib/libcodec2_hidl@1.1-rtk.so',
        'vendor/lib/libcodec2_hidl@1.2-rtk.so',
    ),
}

blob_fixups: blob_fixups_user_type = {}


def fixup(path: str) -> blob_fixup:
    # patchelf 0.18 can leave DT_STRTAB outside PT_LOAD after repeated
    # dependency renames on these ARM32 blobs. This also hides DT_NEEDED
    # from extract-utils, so setup-makefiles.py omits shared_libs.
    return blob_fixups.setdefault(
        path, blob_fixup().patchelf_version('0_17_2')
    )


# Same process HALs: link the graphics.common the platform loads too. The
# camera impl as well, its source-built AIDL dependencies link V7.
for path in (
    'vendor/lib/camera.device.aidl-external-rtk-impl.so',
    'vendor/lib/egl/libGLES_mali.so',
    'vendor/lib/hw/android.hardware.graphics.allocator-V1-arm.so',
    'vendor/lib/hw/android.hardware.graphics.mapper@4.0-impl-arm.so',
):
    fixup(path).replace_needed(
        'android.hardware.graphics.common-V4-ndk.so',
        'android.hardware.graphics.common-V7-ndk.so',
    )

for path in LIBUI_V34_USERS:
    fixup(path).replace_needed('libui.so', 'libui-v34.so')

# Like the camera client fixup in device/rockchip/rk35xx-common, use the
# AIDL versions pulled in by libui-v34. These Codec2 libraries are allocator
# clients; the stock V1 allocator service and implementation keep V1.
for path in (
    'vendor/lib/librtk_c2_adec.so',
    'vendor/lib/librtk_c2_vdec.so',
):
    fixup(path).replace_needed(
        'android.hardware.graphics.allocator-V1-ndk.so',
        'android.hardware.graphics.allocator-V2-ndk.so',
    ).replace_needed(
        'android.hardware.graphics.common-V3-ndk.so',
        'android.hardware.graphics.common-V7-ndk.so',
    )

fixup('vendor/lib/hw/audio.primary.nontuner.so').replace_needed(
    'libaudioroute.so', 'libaudioroute-v34.so'
)

for lib in RENAMED:
    fixup(f'vendor/lib/{lib}-rtk.so').fix_soname()
    for path in RENAMED_USERS[lib]:
        fixup(path).replace_needed(f'{lib}.so', f'{lib}-rtk.so')

# GraphicBufferSource's BufferQueue 2.0 getter was removed from the platform
# helper. Keep the stock Codec2 clients on that interface through our shim.
for path in (
    'vendor/lib/libcodec2_hidl@1.0-rtk.so',
    'vendor/lib/libcodec2_hidl@1.1-rtk.so',
    'vendor/lib/libcodec2_hidl@1.2-rtk.so',
):
    fixup(path).add_needed('libcodec2_hidl_shim_rtk.so')

# SidebandClient still uses Parcel::writeUnpadded@LIBBINDER. The shim keeps
# exact byte counts and preserves the symbol version expected by the blob.
fixup('vendor/lib/libSidebandClient.so').add_needed('libbinder_shim_rtk.so')

# The stock composer imports fmt v7's vformat from libbase. As in the
# Rockchip compatibility fixups, keep it on the snapshot exporting that ABI.
fixup('vendor/bin/hw/android.hardware.graphics.composer3-service.rtk').replace_needed(
    'libbase.so', 'libbase-v33.so'
)

module = ExtractUtilsModule(
    'rtd1325-common',
    'realtek',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
