/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "util/interface.h"

#include <QStringList>

class IGroupSettings
{
public:
    IGroupSettings() = default;
    virtual ~IGroupSettings();
    IGroupSettings(const IGroupSettings&) = default;
    IGroupSettings& operator=(const IGroupSettings&) = default;
    IGroupSettings(IGroupSettings&&) = default;
    IGroupSettings& operator=(IGroupSettings&&) = default;

    virtual QStringList getBlackList() const = 0;
    virtual void setBlackList(const QStringList& blist) = 0;

    virtual bool getShowGroupJoinLeaveMessages() const = 0;
    virtual void setShowGroupJoinLeaveMessages(bool newValue) = 0;

    DECLARE_SIGNAL(blackListChanged, QStringList const& blist);
    DECLARE_SIGNAL(showGroupJoinLeaveMessagesChanged, bool show);
};
