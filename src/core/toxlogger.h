/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include <tox/tox.h>

#include <cstdint>

namespace ToxLogger {
    void onLogMessage(Tox *tox, Tox_Log_Level level, const char *file, uint32_t line,
                      const char *func, const char *message, void *user_data);
}
