/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include <bitset>

// Do not use enum class because we use these as indexes frequently (see ExtensionSet)
struct ExtensionType
{
    enum {
        messages,
        max
    };
};
using ExtensionSet = std::bitset<ExtensionType::max>;
