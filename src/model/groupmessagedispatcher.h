/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "src/core/icoregroupmessagesender.h"
#include "src/core/icoreidhandler.h"
#include "src/model/group.h"
#include "src/model/imessagedispatcher.h"
#include "src/model/message.h"

#include <QObject>
#include <QString>

#include <cstdint>

class IGroupSettings;

class GroupMessageDispatcher : public IMessageDispatcher
{
    Q_OBJECT
public:
    GroupMessageDispatcher(Group& g_, MessageProcessor processor, ICoreIdHandler& idHandler,
                           ICoreGroupMessageSender& messageSender,
                           const IGroupSettings& groupSettings);

    std::pair<DispatchedMessageId, DispatchedMessageId> sendMessage(bool isAction,
                                                                    QString const& content) override;

    std::pair<DispatchedMessageId, DispatchedMessageId>
    sendExtendedMessage(const QString& content, ExtensionSet extensions) override;
    void onMessageReceived(ToxPk const& sender, bool isAction, QString const& content);

private:
    Group& group;
    MessageProcessor processor;
    ICoreIdHandler& idHandler;
    ICoreGroupMessageSender& messageSender;
    const IGroupSettings& groupSettings;
    DispatchedMessageId nextMessageId{0};
};
