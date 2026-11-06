#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

COMMON_PATH := device/realtek/rtd1325-common

## A/B
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/launch_with_vendor_ramdisk.mk)

AB_OTA_POSTINSTALL_CONFIG += \
    RUN_POSTINSTALL_system=true \
    POSTINSTALL_PATH_system=system/bin/otapreopt_script \
    FILESYSTEM_TYPE_system=erofs \
    POSTINSTALL_OPTIONAL_system=true

PRODUCT_PACKAGES += \
    checkpoint_gc \
    otapreopt_script \
    update_engine \
    update_engine_sideload \
    update_verifier

PRODUCT_PACKAGES_DEBUG += \
    update_engine_client

## AAPT
PRODUCT_AAPT_CONFIG := normal large xlarge tvdpi hdpi xhdpi
PRODUCT_AAPT_PREF_CONFIG := xhdpi

## Attestation
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.device_unique_attestation.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.device_unique_attestation.xml \
    frameworks/native/data/etc/android.hardware.keystore.app_attest_key.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.keystore.app_attest_key.xml \
    frameworks/native/data/etc/android.software.device_id_attestation.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.software.device_id_attestation.xml

## Audio
# The stock HIDL 7.0 audio HAL, its effects, r_submix and usb audio stay
# stock: they load into one process together with audio.primary.nontuner.
# Bluetooth audio is built from source, as on ne-common: its stock copies
# carry the names of AOSP modules that link newer AIDL versions, and are
# dlopen()ed by name, so they can be neither kept nor renamed. It shares no
# library with the stock audio blobs.
PRODUCT_PACKAGES += \
    android.hardware.audio.service.rtk.rc

PRODUCT_COPY_FILES += \
    $(COMMON_PATH)/configs/audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_configuration.xml \
    frameworks/av/services/audiopolicy/config/a2dp_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/a2dp_audio_policy_configuration.xml \
    frameworks/av/services/audiopolicy/config/r_submix_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/r_submix_audio_policy_configuration.xml \
    frameworks/native/data/etc/android.hardware.audio.output.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.audio.output.xml

## Bluetooth
PRODUCT_PACKAGES += \
    android.hardware.bluetooth@1.1-service.rtk.rc \
    android.hardware.bluetooth.audio-impl \
    audio.bluetooth.default

PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.bluetooth.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.bluetooth.xml \
    frameworks/native/data/etc/android.hardware.bluetooth_le.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.bluetooth_le.xml

## Boot control
PRODUCT_PACKAGES += \
    com.android.hardware.boot \
    android.hardware.boot-service.default_recovery

## Camera (USB)
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.camera.external.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.camera.external.xml

## Characteristics
PRODUCT_CHARACTERISTICS := tv

## DRM
PRODUCT_PACKAGES += \
    android.hardware.drm-service.clearkey

## Ethernet
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.ethernet.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.ethernet.xml

## fastbootd
PRODUCT_PACKAGES += \
    fastbootd

## Graphics
# Mali G57 (Valhall), stock gralloc/mapper@4.0 and HWC3
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.opengles.aep.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.opengles.aep.xml \
    frameworks/native/data/etc/android.hardware.vulkan.compute-0.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.vulkan.compute.xml \
    frameworks/native/data/etc/android.hardware.vulkan.level-1.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.vulkan.level.xml \
    frameworks/native/data/etc/android.hardware.vulkan.version-1_3.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.vulkan.version.xml \
    frameworks/native/data/etc/android.software.vulkan.deqp.level-2023-03-01.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.software.vulkan.deqp.level.xml

PRODUCT_PACKAGES += \
    disable_configstore

## HDMI CEC
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.hdmi.cec.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.hdmi.cec.xml

## Health
PRODUCT_PACKAGES += \
    android.hardware.health-service.batteryless \
    android.hardware.health-service.batteryless_recovery

## Init
PRODUCT_PACKAGES += \
    fstab.rtd1325 \
    fstab.rtd1325.vendor_ramdisk \
    fstab.zram.50p \
    init.common.usb.rc \
    init.insmod.cfg \
    init.recovery.rtd1325.rc \
    init.rtd1325.poweralloc.rc \
    init.rtd1325.rc \
    init.rtd1325.tunning.rc \
    init.rtd1325.usb.rc \
    ueventd.rtd1325.rc

## Input
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.gamepad.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.gamepad.xml

## Linker
PRODUCT_VENDOR_LINKER_CONFIG_FRAGMENTS += \
    $(COMMON_PATH)/configs/linker/linker.config.json

## Location
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.location.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.location.xml

## OEM Lock
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += \
    ro.oem_unlock_supported=1

## Overlays
PRODUCT_PACKAGES += \
    FrameworksResRtd1325 \
    WifiResRtd1325

PRODUCT_ENFORCE_RRO_TARGETS := *

## Partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

## Permissions
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.software.verified_boot.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.software.verified_boot.xml

## Shipping API
# Stock vendor: ro.product.first_api_level=34, FCM target level 8
PRODUCT_SHIPPING_API_LEVEL := 34

## Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(COMMON_PATH)

## Trusted applications
# Preserve the mount point for the separate stock TA partition on read-only vendor.
PRODUCT_COPY_FILES += \
    $(COMMON_PATH)/configs/ta/dummy.file:$(TARGET_COPY_OUT_VENDOR)/ta/dummy.file

## Storage
$(call inherit-product, $(SRC_TARGET_DIR)/product/emulated_storage.mk)

## Telephony
# Wi-Fi/Ethernet only box
PRODUCT_PROPERTY_OVERRIDES += \
    ro.radio.noril=true

## USB
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.usb.accessory.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.usb.accessory.xml \
    frameworks/native/data/etc/android.hardware.usb.host.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.usb.host.xml

## Wi-Fi
# The stock AIDL Wi-Fi HAL (with Realtek's libwifi-hal) stays, the
# supplicant and hostapd are built from source.
PRODUCT_PACKAGES += \
    android.hardware.wifi-service.rtk.rc \
    hostapd \
    libwpa_client \
    wpa_supplicant

PRODUCT_COPY_FILES += \
    $(COMMON_PATH)/configs/wifi/wpa_supplicant.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant.conf \
    $(COMMON_PATH)/configs/wifi/p2p_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/p2p_supplicant_overlay.conf \
    $(COMMON_PATH)/configs/wifi/wpa_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant_overlay.conf

PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.wifi.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.xml \
    frameworks/native/data/etc/android.hardware.wifi.direct.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.direct.xml \
    frameworks/native/data/etc/android.hardware.wifi.passpoint.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.passpoint.xml

## Inherit from the common proprietary files makefile
$(call inherit-product, vendor/realtek/rtd1325-common/rtd1325-common-vendor.mk)
