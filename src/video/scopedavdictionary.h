/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2024-2026 The TokTok team.
 */

#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

struct AVDictionary;
class QString;

class ScopedAVDictionary
{
    AVDictionary* options = nullptr;

    class Setter
    {
        AVDictionary** dict_;
        const char* key_;

    public:
        Setter(AVDictionary** dict, const char* key)
            : dict_(dict)
            , key_(key)
        {
        }

        Setter& operator=(const char* value);
        Setter& operator=(const QString& value);

        template <std::size_t N>
        Setter& operator=(const std::array<char, N>& value)
        {
            *this = value.data();
            return *this;
        }

        Setter& operator=(std::int64_t value);
    };

public:
    ScopedAVDictionary() = default;
    ScopedAVDictionary& operator=(const ScopedAVDictionary&) = delete;
    ScopedAVDictionary(const ScopedAVDictionary&) = delete;

    ~ScopedAVDictionary();

    Setter operator[](const char* key);

    AVDictionary** get();
};
