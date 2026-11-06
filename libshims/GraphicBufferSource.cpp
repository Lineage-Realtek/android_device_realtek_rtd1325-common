/*
 * Copyright (C) 2026 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <gui/bufferqueue/2.0/B2HGraphicBufferProducer.h>
#include <media/stagefright/bqhelper/GraphicBufferSource.h>

using android::GraphicBufferSource;
using android::sp;
using android::hardware::graphics::bufferqueue::V2_0::IGraphicBufferProducer;
using android::hardware::graphics::bufferqueue::V2_0::utils::B2HGraphicBufferProducer;

// The stock Codec2 HIDL libraries need the BufferQueue 2.0 getter removed
// from GraphicBufferSource. Preserve its exported name and return type;
// getHGraphicBufferProducer_V1_0() returns a different HIDL interface.
sp<IGraphicBufferProducer> getHGraphicBufferProducerRtk(const GraphicBufferSource* source)
        __asm__("_ZNK7android19GraphicBufferSource25getHGraphicBufferProducerEv");

sp<IGraphicBufferProducer> getHGraphicBufferProducerRtk(const GraphicBufferSource* source) {
    return sp<B2HGraphicBufferProducer>::make(source->getIGraphicBufferProducer());
}
