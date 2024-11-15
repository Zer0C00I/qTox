/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "src/model/notificationdata.h"

#include <libsnore/snore.h>

#include <QObject>

#include <memory>
#include <unordered_set>

class Settings;

class DesktopNotify : public QObject
{
    Q_OBJECT
public:
    explicit DesktopNotify(Settings& settings);

public slots:
    void notifyMessage(const NotificationData& notificationData);

signals:
    void notificationClosed();

private slots:
    void onNotificationClose(Snore::Notification notification);

private:
    Snore::SnoreCore& notifyCore;
    Snore::Application snoreApp;
    Snore::Icon snoreIcon;
    Snore::Notification lastNotification;
    uint latestId;
    Settings& settings;
};
