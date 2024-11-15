/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include "src/model/chat.h"

class Chatroom
{
public:
    Chatroom() = default;
    virtual ~Chatroom();
    Chatroom(const Chatroom&) = default;
    Chatroom& operator=(const Chatroom&) = default;
    Chatroom(Chatroom&&) = default;
    Chatroom& operator=(Chatroom&&) = default;

    virtual Chat* getChat() = 0;
};
