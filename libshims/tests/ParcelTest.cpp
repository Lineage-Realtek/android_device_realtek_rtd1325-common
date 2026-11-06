/*
 * Copyright (C) 2026 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "ParcelCompat.h"

#include <gtest/gtest.h>
#include <array>
#include <cstdint>
#include <cstring>

using android::Parcel;

TEST(ParcelCompat, UnalignedAppendsHaveNoPadding) {
    Parcel parcel;
    const std::array<uint8_t, 6> bytes = {1, 2, 3, 4, 5, 6};
    size_t offset = 0;
    for (size_t len : {1u, 2u, 3u}) {
        ASSERT_EQ(android::NO_ERROR, writeUnpaddedRtk(&parcel, bytes.data() + offset, len));
        offset += len;
        EXPECT_EQ(offset, parcel.dataPosition());
        EXPECT_EQ(offset, parcel.dataSize());
    }
    EXPECT_EQ(0, std::memcmp(parcel.data(), bytes.data(), bytes.size()));
}

TEST(ParcelCompat, OverwritePreservesTrailingBytesAndSize) {
    Parcel parcel;
    const std::array<uint8_t, 8> initial = {0, 1, 2, 3, 4, 5, 6, 7};
    ASSERT_EQ(android::NO_ERROR, parcel.write(initial.data(), initial.size()));
    parcel.setDataPosition(2);
    const uint8_t replacement = 42;
    ASSERT_EQ(android::NO_ERROR, writeUnpaddedRtk(&parcel, &replacement, 1));
    const std::array<uint8_t, 8> expected = {0, 1, 42, 3, 4, 5, 6, 7};
    EXPECT_EQ(3u, parcel.dataPosition());
    EXPECT_EQ(expected.size(), parcel.dataSize());
    EXPECT_EQ(0, std::memcmp(parcel.data(), expected.data(), expected.size()));
}

TEST(ParcelCompat, WriteAcrossEndGrowsByExactLength) {
    Parcel parcel;
    const std::array<uint8_t, 4> initial = {1, 2, 3, 4};
    ASSERT_EQ(android::NO_ERROR, parcel.write(initial.data(), initial.size()));
    parcel.setDataPosition(3);
    const std::array<uint8_t, 3> replacement = {7, 8, 9};
    ASSERT_EQ(android::NO_ERROR, writeUnpaddedRtk(&parcel, replacement.data(), replacement.size()));
    const std::array<uint8_t, 6> expected = {1, 2, 3, 7, 8, 9};
    EXPECT_EQ(expected.size(), parcel.dataPosition());
    EXPECT_EQ(expected.size(), parcel.dataSize());
    EXPECT_EQ(0, std::memcmp(parcel.data(), expected.data(), expected.size()));
}

TEST(ParcelCompat, EmptyWriteIsANoOp) {
    Parcel parcel;
    EXPECT_EQ(android::NO_ERROR, writeUnpaddedRtk(&parcel, nullptr, 0));
    EXPECT_EQ(0u, parcel.dataPosition());
    EXPECT_EQ(0u, parcel.dataSize());
}

TEST(ParcelCompat, OversizedWriteDoesNotModifyParcel) {
    Parcel parcel;
    ASSERT_EQ(android::NO_ERROR, parcel.writeInt32(123));
    EXPECT_EQ(android::BAD_VALUE, writeUnpaddedRtk(&parcel, nullptr, size_t(INT32_MAX) + 1));
    EXPECT_EQ(4u, parcel.dataPosition());
    EXPECT_EQ(4u, parcel.dataSize());
    parcel.setDataPosition(0);
    EXPECT_EQ(123, parcel.readInt32());
}

TEST(ParcelCompat, RejectsPositionPlusLengthOverflow) {
    Parcel parcel;
    parcel.setDataPosition(INT32_MAX);
    EXPECT_EQ(android::BAD_VALUE, writeUnpaddedRtk(&parcel, nullptr, 1));
    EXPECT_EQ(size_t(INT32_MAX), parcel.dataPosition());
}
