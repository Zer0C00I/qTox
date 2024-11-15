/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include <QString>

class ICoreGroupMessageSender
{
public:
    ICoreGroupMessageSender() = default;
    virtual ~ICoreGroupMessageSender();
    ICoreGroupMessageSender(const ICoreGroupMessageSender&) = default;
    ICoreGroupMessageSender& operator=(const ICoreGroupMessageSender&) = default;
    ICoreGroupMessageSender(ICoreGroupMessageSender&&) = default;
    ICoreGroupMessageSender& operator=(ICoreGroupMessageSender&&) = default;

    virtual void sendGroupAction(int groupId, const QString& message) = 0;
    virtual void sendGroupMessage(int groupId, const QString& message) = 0;
};
