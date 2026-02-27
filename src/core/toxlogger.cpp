/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024-2026 The TokTok team.
 */

#include "toxlogger.h"

#include <QDebug>
#include <QLoggingCategory>

#include <tox/tox.h>

namespace ToxLogger {
namespace {

Q_LOGGING_CATEGORY(toxcore, "tox.core")

} // namespace

/**
 * @brief Log message handler for toxcore log messages
 * @note See tox.h for the parameter definitions
 */
void onLogMessage(Tox* tox, Tox_Log_Level level, const char* file, uint32_t line, const char* func,
                  const char* message, void* user_data)
{
    std::ignore = tox;
    std::ignore = user_data;

    const int lineInt = static_cast<int>(line);
    switch (level) {
    case TOX_LOG_LEVEL_TRACE:
        // trace level generates too much noise to enable by default
        QMessageLogger(file, lineInt, func).debug(toxcore) << message;
        return;
    case TOX_LOG_LEVEL_DEBUG:
        QMessageLogger(file, lineInt, func).debug(toxcore) << message;
        break;
    case TOX_LOG_LEVEL_INFO:
        QMessageLogger(file, lineInt, func).info(toxcore) << message;
        break;
    case TOX_LOG_LEVEL_WARNING:
        QMessageLogger(file, lineInt, func).warning(toxcore) << message;
        break;
    case TOX_LOG_LEVEL_ERROR:
        QMessageLogger(file, lineInt, func).critical(toxcore) << message;
        break;
    }
}

} // namespace ToxLogger
