/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */


#pragma once

#include <QByteArray>
#include <QString>
#include <cstdint>

QString dataToString(QByteArray data);
uint64_t dataToUint64(const QByteArray& data);
int dataToVInt(const QByteArray& data);
size_t dataToVUint(const QByteArray& data);
unsigned getVUint32Size(QByteArray data);
QByteArray vintToData(int num);
QByteArray vuintToData(size_t num);
