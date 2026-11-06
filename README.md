# device/realtek/rtd1325-common

Shared LineageOS 23.2 (Android 16) tree for Realtek RTD1325 Android TV boxes,
built on the stock Android 14 vendor. Modelled on `device/amlogic/ne-common`,
which has the same shape: Android 14 vendor, GKI 5.15, A/B with Virtual A/B,
32-bit userspace on a 64-bit kernel.

| Layer | Holds |
| --- | --- |
| this directory | BoardConfig/product makefiles, blob list and extract scripts, init/fstab/ueventd, VINTF, sepolicy, overlays, tools |
| board tree (e.g. `device/realtek/rtx2`) | super size, density, the prebuilt kernel wiring, board-only blobs (remote keylayouts) |
| `device/realtek/<board>-kernel` | the prebuilt kernel, dtb, dtbo and modules of that board |

## Platform

| | |
| --- | --- |
| SoC | RTD1325 (4x Cortex-A55), Mali-G57, 4 GiB |
| Userspace | 32-bit only: the vendor has no `lib64`, `ro.zygote=zygote32` |
| Kernel | GKI `5.15.148-android14-11`, prebuilt |
| Boot | header v4: `boot` (kernel), `init_boot` (generic ramdisk), `vendor_boot` (vendor ramdisk, dtb, first stage modules) |
| Partitions | A/B, Virtual A/B with compression, 1920 MiB `super`, erofs |
| Stock | `Google/RTD1325_AOSP_BOX/ross:14/UD2A.231203.054`, vendor API 34, FCM level 8, SPL 2024-03-05 |

## Kernel

Prebuilt, from the stock OTA. `tools/import-prebuilt-kernel.sh <dump> <dir>`
copies `Image.gz`, the vendor_boot dtb, `dtbo.img` and the three module sets
with their `modules.load` lists into a board's kernel directory.

* `vendor_boot` modules are loaded by first stage init.
  The board also bundles its display/RPC, remote and USB drivers here,
  selecting them through `modules.load.recovery`. Recovery does not run
  the normal vendor module loader. Its init rc selects the stock USB
  controller and device role for the configfs ADB/fastboot gadget.
  The RT-X2 product sets `WITH_ADB_INSECURE := true` for bring-up so ADB
  logs can be collected before the UI and `/data` work.
  Recovery uses `BGRA_8888`, which minui maps to the primary plane's
  supported DRM ARGB8888 format. RGBX/XBGR8888 fails `drmModeSetCrtc` even
  though framebuffer allocation and `drmModeAddFB2` succeed.
* `vendor_dlkm` modules are **not** loaded by init. Like stock,
  `init.insmod.sh` (started from `init.rtd1325.rc` in early-init) walks
  `init.insmod.cfg` and `modprobe`s them from `/vendor/lib/modules`, then runs
  `wifi_auto_insmod`, which probes the SDIO/USB/PCIe id of the Wi-Fi chip and
  sets `vendor.rtk.<chip>=1`; `init.rtd1325.rc` reacts to that by loading the
  matching driver and starting the Bluetooth HAL.
* `system_dlkm` holds GKI modules, 12 of them signed. They are installed as
  they are; vendor modules are unsigned and get stripped.

The kernel in the dump (`-g1a7b17ef9336-dirty`) is newer than the one some
boxes run (`-gdd1432f3ba88-dirty`); all three module sets in the dump match
the dump's kernel. When testing the built `vendor_boot.img`, also use the
same build's `boot.img` so the kernel and first stage modules match.

`init_boot` must also use a v4 header, matching stock. Its image rule uses
`BOARD_MKBOOTIMG_INIT_ARGS`, separately from `BOARD_MKBOOTIMG_ARGS`; setting
`BOARD_INIT_BOOT_HEADER_VERSION` alone does not select the header version.

## Verified boot -- unlock first

Stock `vbmeta` is signed with a Realtek key the bootloader trusts through the
`vbmeta_cert` partition, and the device reports `locked`/`green`. These images
are signed with the AOSP test keys and `vbmeta` carries `--flags 1`, so the
bootloader **must be unlocked** (`ro.oem_unlock_supported=1`; enable OEM
unlocking in developer options, then `fastboot flashing unlock`). The stock
chain layout is kept: `vbmeta_system` at rollback location 2,
`vbmeta_vendor` at 3.

Only the hashtree-disabled bit is set. Do not use `--flags 3`: the
verification-disabled bit makes libavb omit `androidboot.vbmeta.size`,
`hash_alg` and `digest`. With this LK normal boot, first-stage init then
rejects the missing digest and aborts before mounting `/system`. Keeping
metadata verification enabled lets LK generate those boot parameters.

LK appends `androidboot.selinux=permissive` to bootconfig. Do not also set
it in `BOARD_BOOTCONFIG`: the kernel rejects duplicate assignments and
discards the whole bootconfig, including the bootloader's slot suffix.
This causes `Error updating for slotselect` and a recovery crash loop even
though fstab is present.

Normal-boot USB uses configfs from the fs action and waits for adbd's
FunctionFS readiness signal before binding the gadget. On debuggable builds,
ADB selects the recovery-tested controller and device role after vendor
modules finish loading. A bounded logcat capture in
`/metadata/rtx2-bringup/` provides logs if USB is unavailable.

The primary audio selector is `ro.hardware.audio.primary=nontuner`; without
it, libhardware falls back to the silent `audio.primary.default` stub. The
common BoardConfig enables `skip_speaker_layout_channel_mask_field` so the
source-built HIDL converters retain the stock Android 14 native structure
layout. Otherwise `getAudioPort` overwrites the stock wrapper's stack.

The device-owned audio policy currently omits the stock HW_AV_SYNC mix ports
and their route references, which caused AudioFlinger to abort while the
silent stub was selected. These paths still need validation with the real
HAL. Regular PCM, USB and Bluetooth policy paths remain present.

## Vendor blobs

`/vendor/ta` is the mount point for the stock `ta_a`/`ta_b` partition.
Keep `configs/ta/dummy.file` installed there: EROFS vendor cannot create
a missing directory at boot. Without it, the TA mount fails and KeyMint
returns secure-hardware communication errors during userdata encryption.

`proprietary-files.txt` was drafted with

    tools/gen-proprietary-files.py <dump> -o draft.txt \
        --module-info out/target/product/<any earlier build>/module-info.json \
        --top $ANDROID_BUILD_TOP -v

and then edited by hand. The generator drops what LineageOS builds or this
tree carries (toybox links, metadata, our init/fstab, the HALs built from
source, AIDL/HIDL interface libraries that exist as Soong modules, configs
byte-identical to their `frameworks/` copy), sorts the rest into sections and
resolves every kept ELF's `DT_NEEDED` against blobs, LLNDK and the module
index -- anything unresolved would be a `check_elf_files` build error. Keep
its rules (`SOURCE_BUILT`, `TREE_FILES`) in sync with hand edits, so a rerun
against a newer dump gives a diff worth reading.

Built from source rather than taken from stock: boot control, health
(batteryless), ClearKey DRM, `wpa_supplicant`/`hostapd`, the r_submix/usb
audio HALs. Dropped: the RIL libraries (no modem), ClearKey CAS, the stock
`dhcpcd`/`iprenew` rc files (they start `/system/bin/dhcpcd`, which LineageOS
does not ship), the logcatcher scripts.

Everything else stays stock. The rule from rk35xx-common applies: migrate a
whole *process*, never half of one. That is why the audio HAL, its effects
and Bluetooth audio all stay stock together.

Extract from the board tree, pointing at a directory that holds **only
`vendor/`** (extract-utils moves a system-as-root `system/` it finds):

    mkdir /tmp/rtd1325 && cp -a <dump>/vendor /tmp/rtd1325/
    cd ../rtx2 && ./extract-files.py /tmp/rtd1325

## Blobs against a newer platform

There is no VNDK any more, so a blob links whatever Android 16 builds. Fixups
in `extract-files.py`:

* Same-process graphics (`libGLES_mali`, gralloc mapper and allocator impl)
  link `android.hardware.graphics.common-V7-ndk` instead of V4, as on
  ne-common.
* Blobs linking `libui`, none of which is loaded by a framework process, get
  `libui-v34` from `hardware/lineage/compat`; `audio.primary.nontuner` gets
  `libaudioroute-v34`.
* Codec2 audio/video decoder clients link graphics allocator V2 and graphics
  common V7, matching `libui-v34` and avoiding mixed AIDL versions in their
  dependency graph. The stock V1 allocator service keeps its V1 interface.
* The three stock Codec2 HIDL libraries link `libcodec2_hidl_shim_rtk`. It
  restores `GraphicBufferSource::getHGraphicBufferProducer()` by wrapping
  the current native producer in the BufferQueue 2.0 adapter, as the old
  platform method did. The remaining V1.0 getter returns another interface.
* `libSidebandClient` links `libbinder_shim_rtk` for the versioned
  `Parcel::writeUnpadded` symbol. It preserves exact byte counts and existing
  trailing data, using the current Parcel's public APIs to manage storage.
* The stock composer links `libbase-v33` for its imported fmt v7 formatting
  function, which the current platform `libbase` no longer exports.

The ELF fixups use `patchelf` 0.17.2. Version 0.18 can put `DT_STRTAB`
outside every `PT_LOAD` segment after repeated dependency renames on these
ARM32 blobs. That prevents extract-utils from reading `DT_NEEDED`, leaving
the generated `Android.bp` without `shared_libs`. If blobs were extracted
with 0.18, re-extract from the stock dump with the fixed script before
running `setup-makefiles.py`; regenerating makefiles alone cannot repair
the malformed ELF files.

After a build, run the checkers ported from rk35xx-common:

    tools/check-vendor-deps.py $OUT       # DT_NEEDED actually on the image?
    tools/check-vendor-symbols.py $OUT    # every undefined symbol resolves?
    tools/check-vendor-vtables.py $OUT <dump> vendor/realtek/rtd1325-common/proprietary

The vtable check is the one that finds ABI drift in libraries such as
`libstagefright_foundation`, `libcodec2_vndk` users or `libutils` that a
symbol check passes.

## SELinux

Bring-up policy. It labels partitions, device nodes, `/data/vendor` and every
HAL binary (onto the AOSP `hal_*_default` domains, as stock did) and gives the
Realtek daemons their own domains, declared `permissive`. The stock policy
(`vendor/etc/selinux/vendor_sepolicy.cil`, ~3500 allow rules) is the
reference for writing real rules from the denials.
