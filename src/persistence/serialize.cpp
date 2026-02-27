/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024-2026 The TokTok team.
 */

#include "src/persistence/serialize.h"

#include <climits>
#include <limits>

/**
 * @file serialize.cpp
 *
 * These functions are hardened against any input data and will not crash.
 * They will return an empty string or 0 if the data is invalid. The 0 was
 * chosen (as opposed to e.g. -1) to avoid potential out-of-bounds problems
 * in the caller.
 *
 * There is no error handling here. Callers should ideally only pass valid
 * data to these functions.
 */

namespace {
constexpr size_t intWidth = sizeof(int) * CHAR_BIT;
}

int dataToVInt(const QByteArray& data)
{
    uint32_t result = 0;
    size_t shift = 0;
    int i = 0;
    char num3 = '\0';
    do {
        if (i >= data.size()) {
            return 0;
        }
        num3 = data[i++];
        if (shift >= 32) {
            return 0;
        }
        // Use unsigned arithmetic to avoid signed integer overflow UB.
        // At shift=28, only 4 bits remain before the 32-bit boundary;
        // reject any 7-bit value that would not fit in those remaining bits.
        const uint32_t bits = static_cast<uint8_t>(num3) & 0x7fu;
        if (bits > (std::numeric_limits<uint32_t>::max() >> shift)) {
            return 0;
        }
        result |= bits << shift;
        shift += 7;
    } while ((num3 & 0x80) != 0);
    return static_cast<int>(result);
}

QByteArray vintToData(int num)
{
    QByteArray data(sizeof(int), 0);
    // Write the size in a Uint of variable length (8-32 bits)
    int i = 0;
    while (num >= 0x80) {
        if (i >= data.size()) {
            return {};
        }
        data[i] = static_cast<char>(num | 0x80);
        ++i;
        num = num >> 7;
    }
    if (i >= data.size()) {
        return {};
    }
    data[i] = static_cast<char>(num);
    data.resize(i + 1);
    return data;
}
