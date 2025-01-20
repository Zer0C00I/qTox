/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2025 The TokTok team.
 */

#pragma once

#include "src/widget/tool/abstractscreenshotgrabber.h"

#include <QVariantMap>

#include <memory>

#if QT_CONFIG(dbus)
/** @brief Grabs screenshot using org.freedesktop.portal.Screenshot.
 *
 * https://docs.flatpak.org/en/latest/portal-api-reference.html#gdbus-org.freedesktop.portal.Screenshot
 */
class DBusScreenshotGrabber : public AbstractScreenshotGrabber
{
    Q_OBJECT

public:
    // Don't use these directly, use create() instead.
    explicit DBusScreenshotGrabber(QWidget* parent);
    ~DBusScreenshotGrabber() override;

    // Create a screenshot grabber. Returns nullptr if no DBus connection could be established.
    static DBusScreenshotGrabber* create(QWidget* parent);

    bool isValid() const;
    void showGrabber() override;

private slots:
    void screenshotResponse(uint response, QVariantMap results);

private:
    struct Data;
    std::unique_ptr<Data> d;
};
#endif // QT_CONFIG(dbus)
