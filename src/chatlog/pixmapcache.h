/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2015-2019 by The qTox Project Contributors
 * Copyright © 2024-2025 The TokTok team.
 */

#pragma once

#include <QHash>
#include <QIcon>
#include <QPixmap>

class PixmapCache
{
public:
    QPixmap get(const QString& filename, QSize size);
    static PixmapCache& getInstance();

protected:
    PixmapCache() {}
    PixmapCache(PixmapCache&) = delete;
    PixmapCache& operator=(const PixmapCache&) = delete;

private:
    QHash<QString, QIcon> cache;
};
