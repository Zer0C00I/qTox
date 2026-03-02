/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2024-2026 The TokTok team.
 */

#pragma once

#include <QObject>

#include <memory>

class DesktopNotifyBackend : public QObject
{
    Q_OBJECT

public:
    explicit DesktopNotifyBackend(QObject* parent);
    ~DesktopNotifyBackend() override;
    bool showMessage(const QString& title, const QString& message, const QString& category,
                     const QPixmap& pixmap);

signals:
    void messageClicked();

private slots:
    // NOLINTNEXTLINE(performance-unnecessary-value-param) -- Qt DBus slot, string-based SLOT() requires by-value params
    void notificationActionInvoked(QString actionKey, QString actionValue);
    // NOLINTNEXTLINE(performance-unnecessary-value-param)
    void notificationActionInvoked(uint actionKey, QString actionValue);

private:
    struct Private;
    const std::unique_ptr<Private> d;
};
