/*
 * Copyright (C) 2026 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "ParcelCompat.h"

#include <algorithm>
#include <cstdint>
#include <cstring>

android::status_t writeUnpaddedRtk(android::Parcel* parcel, const void* data, size_t len) {
    const size_t start = parcel->dataPosition();
    if (len > INT32_MAX || start > INT32_MAX - len) {
        return android::BAD_VALUE;
    }
    if (len == 0) {
        return android::NO_ERROR;
    }

    const size_t end = start + len;
    // setDataSize reserves space and takes ownership of externally owned data.
    // Keeping the original size preserves bytes and Binder objects after an
    // overwrite. Unlike writeInplace(), this does not zero alignment padding.
    const android::status_t status = parcel->setDataSize(std::max(parcel->dataSize(), end));
    if (status != android::NO_ERROR) {
        return status;
    }
    std::memcpy(const_cast<uint8_t*>(parcel->data()) + start, data, len);
    parcel->setDataPosition(end);
    return android::NO_ERROR;
}
