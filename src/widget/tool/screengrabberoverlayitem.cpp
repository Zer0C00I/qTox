/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2015-2019 by The qTox Project Contributors
 * Copyright © 2024-2026 The TokTok team.
 */

#include "screengrabberoverlayitem.h"

#include "screenshotgrabber.h"

#include <QGraphicsSceneMouseEvent>
#include <QPainter>
#include <QPen>
#include <QStyleOptionGraphicsItem>

ScreenGrabberOverlayItem::ScreenGrabberOverlayItem(ScreenshotGrabber* grabber)
    : screenshotGrabber(grabber)
{
    const QBrush overlayBrush(QColor(0x00, 0x00, 0x00, 0x70)); // Translucent black

    setCursor(QCursor(Qt::CrossCursor));
    setBrush(overlayBrush);
    setPen(QPen(Qt::NoPen));
}

ScreenGrabberOverlayItem::~ScreenGrabberOverlayItem() = default;

void ScreenGrabberOverlayItem::setChosenRect(QRect rect)
{
    const QRect oldRect = chosenRect;
    chosenRect = rect;
    update(oldRect.united(rect));
}

void ScreenGrabberOverlayItem::mousePressEvent(QGraphicsSceneMouseEvent* event)
{
    if (event->button() == Qt::LeftButton)
        screenshotGrabber->beginRectChooser(event);
}

void ScreenGrabberOverlayItem::paint(QPainter* painter, const QStyleOptionGraphicsItem* option,
                                     QWidget* widget)
{
    std::ignore = option;
    std::ignore = widget;
    painter->setBrush(brush());
    painter->setPen(pen());

    const QRectF self = rect();
    const qreal leftX = chosenRect.x();
    const qreal rightX = chosenRect.x() + chosenRect.width();
    const qreal topY = chosenRect.y();
    const qreal bottomY = chosenRect.y() + chosenRect.height();

    painter->drawRect(0, 0, static_cast<int>(leftX), static_cast<int>(self.height()));                                                        // Left of chosen
    painter->drawRect(static_cast<int>(rightX), 0, static_cast<int>(self.width() - rightX), static_cast<int>(self.height())); // Right of chosen
    painter->drawRect(static_cast<int>(leftX), 0, chosenRect.width(), static_cast<int>(topY));                                 // Top of chosen
    painter->drawRect(static_cast<int>(leftX), static_cast<int>(bottomY), chosenRect.width(),
                      static_cast<int>(self.height() - bottomY)); // Bottom of chosen
}
