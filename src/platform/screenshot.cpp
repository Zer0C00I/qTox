/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2025 The TokTok team.
 */

#include "screenshot.h"

#include "screenshot_dbus.h"

#include "src/widget/tool/abstractscreenshotgrabber.h"

AbstractScreenshotGrabber* Platform::createScreenshotGrabber(QWidget* parent)
{
#if QT_CONFIG(dbus)
    return DBusScreenshotGrabber::create(parent);
#else
    std::ignore = parent;
    return nullptr;
#endif
}
