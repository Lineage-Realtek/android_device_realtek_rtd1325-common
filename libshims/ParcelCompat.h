/*
 * Copyright (C) 2026 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <binder/Parcel.h>

// Export the old member-function ABI without depending on Parcel's private
// layout. A member call passes the Parcel pointer as its first argument.
android::status_t writeUnpaddedRtk(android::Parcel* parcel, const void* data, size_t len)
#if defined(__LP64__)
        __asm__("_ZN7android6Parcel13writeUnpaddedEPKvm");
#else
        __asm__("_ZN7android6Parcel13writeUnpaddedEPKvj");
#endif
