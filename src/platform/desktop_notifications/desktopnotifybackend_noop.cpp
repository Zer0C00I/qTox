/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2024 The TokTok team.
 */

#include "desktopnotifybackend.h"

#if !QT_CONFIG(dbus)
struct DesktopNotifyBackend::Private
{};

DesktopNotifyBackend::DesktopNotifyBackend(QObject* parent)
    : QObject(parent)
    , d{nullptr}
{
}
DesktopNotifyBackend::~DesktopNotifyBackend() = default;

bool DesktopNotifyBackend::showMessage(const QString& title, const QString& message,
                                       const QPixmap& pixmap)
{
    std::ignore = title;
    std::ignore = message;
    std::ignore = pixmap;
    // Always fail, fall back to QSystemTrayIcon.
    return false;
}
#endif // !QT_CONFIG(dbus)
