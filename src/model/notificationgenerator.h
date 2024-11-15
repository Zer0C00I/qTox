/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2020 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once


#include "notificationdata.h"
#include "friend.h"
#include "group.h"

#include "src/persistence/inotificationsettings.h"
#include "src/persistence/profile.h"

#include <QObject>
#include <QHash>

class NotificationGenerator : public QObject
{
    Q_OBJECT

public:
    NotificationGenerator(
        INotificationSettings const& notificationSettings_,
        // Optional profile input to lookup avatars. Avatar lookup is not
        // currently mockable so we allow profile to be nullptr for unit
        // testing
        Profile* profile_);
    virtual ~NotificationGenerator();
    NotificationGenerator(const NotificationGenerator&) = delete;
    NotificationGenerator& operator=(const NotificationGenerator&) = delete;
    NotificationGenerator(NotificationGenerator&&) = delete;
    NotificationGenerator& operator=(NotificationGenerator&&) = delete;

    NotificationData friendMessageNotification(const Friend* f, const QString& message);
    NotificationData groupMessageNotification(const Group* g, const ToxPk& sender, const QString& message);
    NotificationData fileTransferNotification(const Friend* f, const QString& filename, size_t fileSize);
    NotificationData groupInvitationNotification(const Friend* from);
    NotificationData friendRequestNotification(const ToxPk& sender, const QString& message);

public slots:
    void onNotificationActivated();

private:
    INotificationSettings const& notificationSettings;
    Profile* profile;
    QHash<const Friend*, size_t> friendNotifications;
    QHash<const Group*, size_t> groupNotifications;
};
