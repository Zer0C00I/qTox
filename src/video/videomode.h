/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2015-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include <QRect>
#include <cstdint>

struct VideoMode
{
    int width, height;
    int x, y;
    float FPS = -1.0f;
    uint32_t pixel_format = 0;

    VideoMode(int width = 0, int height = 0, int x = 0, int y = 0, float FPS = -1.0f);

    explicit VideoMode(QRect rect);

    QRect toRect() const;

    operator bool() const;
    bool operator==(const VideoMode& other) const;
    uint32_t norm(const VideoMode& other) const;
    uint32_t tolerance() const;
};
