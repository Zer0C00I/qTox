/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "src/core/groupid.h"

class Core;
template <class A, class B>
class QHash;
template <class T>
class QList;
class Group;
class QString;
class FriendList;

class GroupList
{
public:
    Group* addGroup(Core& core, int groupNum, const GroupId& persistentGroupId, const QString& name,
                    bool isAvGroupchat, const QString& selfName, FriendList& friendList);
    Group* findGroup(const GroupId& groupId);
    const GroupId& id2Key(uint32_t groupNum);
    void removeGroup(const GroupId& groupId, bool fake = false);
    QList<Group*> getAllGroups();
    void clear();

private:
    QHash<const GroupId, Group*> groupList;
    QHash<uint32_t, GroupId> id2key;
};
