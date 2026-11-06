#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

COMMON_PATH := device/realtek/rtd1325-common

## A/B
AB_OTA_UPDATER := true

AB_OTA_PARTITIONS += \
    boot \
    dtbo \
    init_boot \
    odm \
    odm_dlkm \
    product \
    system \
    system_dlkm \
    system_ext \
    vbmeta \
    vbmeta_system \
    vbmeta_vendor \
    vendor \
    vendor_boot \
    vendor_dlkm

## Architecture
# The vendor partition is 32-bit only (ro.zygote=zygote32, no vendor/lib64),
# on top of an arm64 GKI kernel.
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a55

TARGET_KERNEL_ARCH := arm64

## Android Verified Boot
# Stock vbmeta is signed with a Realtek key the bootloader trusts through
# vbmeta_cert, so these images only boot with the bootloader unlocked
# (ro.oem_unlock_supported=1, "fastboot flashing unlock"). vbmeta keeps the
# stock layout: vbmeta_system at rollback location 2, vbmeta_vendor at 3.
BOARD_AVB_ENABLE := true
# Disable dm-verity for bring-up, but retain AVB metadata verification.
# flags=3 omits LK vbmeta digest parameters and first-stage init aborts.
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 1
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_ROLLBACK_INDEX := 0

BOARD_AVB_VBMETA_SYSTEM := product system system_dlkm system_ext
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2

BOARD_AVB_VBMETA_VENDOR := odm odm_dlkm vendor vendor_dlkm
BOARD_AVB_VBMETA_VENDOR_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_VENDOR_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX_LOCATION := 3

# GSI keys live in vendor_boot, stock fstab uses avb_keys=/avb
BOARD_MOVE_GSI_AVB_KEYS_TO_VENDOR_BOOT := true

## Audio
BOARD_USES_ALSA_AUDIO := true
# The stock Android 14 HAL uses audio_port_config without the speaker layout field.
$(call soong_config_set_bool,android_hardware_audio,skip_speaker_layout_channel_mask_field,true)

## Bluetooth
BOARD_HAVE_BLUETOOTH := true

## Boot image
# GKI: boot holds only the kernel, init_boot the generic ramdisk,
# vendor_boot the vendor ramdisk, the first stage modules and the dtb.
BOARD_BOOT_HEADER_VERSION := 4
BOARD_INIT_BOOT_HEADER_VERSION := 4
# init_boot has its own mkbootimg arguments; the version variable alone
# is not consumed by the image rule and would leave the header at v0.
BOARD_MKBOOTIMG_INIT_ARGS += --header_version $(BOARD_INIT_BOOT_HEADER_VERSION)
BOARD_KERNEL_PAGESIZE := 2048
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_IMAGE_NAME := Image.gz
# Load addresses of the stock vendor_boot (unpack_bootimg --format mkbootimg)
BOARD_MKBOOTIMG_ARGS += \
    --header_version $(BOARD_BOOT_HEADER_VERSION) \
    --kernel_offset 0x31008000 \
    --ramdisk_offset 0x09000000 \
    --tags_offset 0x00000100 \
    --dtb_offset 0x03000000
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_RAMDISK_USE_LZ4 := true
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true

## Kernel
# The bootloader passes console, earlycon, firmware_class.path and friends;
# stock vendor_boot only adds "bootconfig".
BOARD_KERNEL_CMDLINE := bootconfig

BOARD_BOOTCONFIG += \
    androidboot.hardware=rtd1325 \
    androidboot.boot_devices=soc@0/98000000.rbus/98012000.emmc \
    androidboot.storage=emmc \
    androidboot.dynamic_partitions=true

# LK appends androidboot.selinux=permissive at boot. Defining it here too
# makes the kernel reject the entire bootconfig, losing the slot suffix.

TARGET_KERNEL_VERSION := 5.15

## Partitions
BOARD_FLASH_BLOCK_SIZE := 131072
BOARD_USES_METADATA_PARTITION := true

BOARD_BOOTIMAGE_PARTITION_SIZE := 47185920
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE := 4194304
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 33554432
BOARD_DTBOIMG_PARTITION_SIZE := 8388608

BOARD_USES_ODM_DLKMIMAGE := true
BOARD_USES_SYSTEM_DLKMIMAGE := true
BOARD_USES_VENDOR_DLKMIMAGE := true

SSI_PARTITIONS := product system system_ext
TREBLE_PARTITIONS := odm odm_dlkm system_dlkm vendor vendor_dlkm
ALL_PARTITIONS := $(SSI_PARTITIONS) $(TREBLE_PARTITIONS)

$(foreach p, $(call to-upper, $(ALL_PARTITIONS)), \
    $(eval BOARD_$(p)IMAGE_FILE_SYSTEM_TYPE := erofs) \
    $(eval TARGET_COPY_OUT_$(p) := $(call to-lower, $(p))))

BOARD_EROFS_PCLUSTER_SIZE := 262144

# Stock super is 1920 MiB with a single main_group_[ab]; with Virtual A/B
# only one slot lives in super.
BOARD_BUILD_SUPER_IMAGE_BY_DEFAULT := true
BOARD_SUPER_PARTITION_GROUPS := realtek_dynamic_partitions
BOARD_REALTEK_DYNAMIC_PARTITIONS_PARTITION_LIST := $(ALL_PARTITIONS)
BOARD_REALTEK_DYNAMIC_PARTITIONS_SIZE = $(shell echo $$(($(BOARD_SUPER_PARTITION_SIZE) - 4194304)))

TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true

include vendor/lineage/config/BoardConfigReservedSize.mk

## Platform
TARGET_BOARD_PLATFORM := rtd1325
TARGET_BOOTLOADER_BOARD_NAME := rtd1325

## Properties
TARGET_VENDOR_PROP += $(COMMON_PATH)/vendor.prop

## Recovery
TARGET_NO_RECOVERY := true
TARGET_RECOVERY_FSTAB := $(COMMON_PATH)/init/fstab.rtd1325
# minui maps BGRA byte order to DRM ARGB8888, supported by the primary plane.
# RGBX maps to XBGR8888, which the Realtek driver rejects at modeset time.
TARGET_RECOVERY_PIXEL_FORMAT := BGRA_8888
TARGET_RECOVERY_DENSITY := 200dpi

## SELinux
BOARD_VENDOR_SEPOLICY_DIRS += $(COMMON_PATH)/sepolicy/vendor

## Vendor security patch level, matching the dump
VENDOR_SECURITY_PATCH := 2024-03-05

## VINTF
DEVICE_MANIFEST_FILE += $(COMMON_PATH)/manifest.xml
DEVICE_MATRIX_FILE := $(COMMON_PATH)/compatibility_matrix.xml
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(COMMON_PATH)/vendor_framework_compatibility_matrix.xml

## Wi-Fi
# No BOARD_WLAN_DEVICE: the stock Wi-Fi HAL and its libwifi-hal are used, and
# "realtek" would point libwifi-hal at hardware/realtek, which is not synced.
BOARD_HOSTAPD_DRIVER := NL80211
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
WPA_SUPPLICANT_VERSION := VER_0_8_X
WIFI_HIDL_UNIFIED_SUPPLICANT_SERVICE_RC_ENTRY := true

## Include the common proprietary BoardConfig makefile
include vendor/realtek/rtd1325-common/BoardConfigVendor.mk
