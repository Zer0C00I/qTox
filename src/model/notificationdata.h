/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2020 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include <QString>
#include <QPixmap>

struct NotificationData
{
    QString title;
    QString message;
    QPixmap pixmap;
};
