/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2017-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#ifdef QTOX_PLATFORM_EXT

typedef struct _XDisplay Display;

namespace Platform {

namespace X11Display {
Display* lock();
void unlock();
} // namespace X11Display

} // namespace Platform

#endif // QTOX_PLATFORM_EXT
