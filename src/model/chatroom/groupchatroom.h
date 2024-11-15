/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "chatroom.h"

#include <QObject>

class Core;
class IDialogsManager;
class Group;
class ToxPk;
class FriendList;

class GroupChatroom : public QObject, public Chatroom
{
    Q_OBJECT
public:
    GroupChatroom(Group* group_, IDialogsManager* dialogsManager_, Core& core_,
        FriendList& friendList);

    Chat* getChat() override;

    Group* getGroup();

    bool hasNewMessage() const;
    void resetEventFlags();

    bool friendExists(const ToxPk& pk);
    void inviteFriend(const ToxPk& pk);

    bool possibleToOpenInNewWindow() const;
    bool canBeRemovedFromWindow() const;
    void removeGroupFromDialogs();

private:
    Group* group{nullptr};
    IDialogsManager* dialogsManager{nullptr};
    Core& core;
    FriendList& friendList;
};
