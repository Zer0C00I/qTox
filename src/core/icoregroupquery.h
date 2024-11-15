/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2013 by Maxim Biro <nurupo.contributions@gmail.com>
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "groupid.h"
#include "toxpk.h"

#include <QString>
#include <QStringList>

#include <cstdint>

class ICoreGroupQuery
{
public:
    ICoreGroupQuery() = default;
    virtual ~ICoreGroupQuery();
    ICoreGroupQuery(const ICoreGroupQuery&) = default;
    ICoreGroupQuery& operator=(const ICoreGroupQuery&) = default;
    ICoreGroupQuery(ICoreGroupQuery&&) = default;
    ICoreGroupQuery& operator=(ICoreGroupQuery&&) = default;

    virtual GroupId getGroupPersistentId(uint32_t groupNumber) const = 0;
    virtual uint32_t getGroupNumberPeers(int groupId) const = 0;
    virtual QString getGroupPeerName(int groupId, int peerId) const = 0;
    virtual ToxPk getGroupPeerPk(int groupId, int peerId) const = 0;
    virtual QStringList getGroupPeerNames(int groupId) const = 0;
    virtual bool getGroupAvEnabled(int groupId) const = 0;
};
