/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2022 by The qTox Project Contributors
 * Copyright © 2024-2025 The TokTok team.
 */

#pragma once

#include "src/persistence/db/rawdatabase.h"
#include "src/persistence/db/upgrades/dbupgrader.h"

#include <QVector>

class ToxPk;

namespace DbTo11 {
bool dbSchema10to11(RawDatabase& db);
bool appendDeduplicatePeersQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
bool getInvalidPeers(RawDatabase& db, std::vector<DbUpgrader::BadEntry>& badPeers);
bool appendSplitPeersQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);


namespace PeersToAuthors {
bool appendPeersToAuthorsQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
void appendCreateNewTablesQueries(QVector<RawDatabase::Query>& upgradeQueries);
bool appendPopulateAuthorQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
bool appendUpdateAliasesFkQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
void appendReplaceOldTablesQueries(QVector<RawDatabase::Query>& upgradeQueries);
} // namespace PeersToAuthors

namespace PeersToChats {
bool appendPeersToChatsQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
void appendCreateNewTablesQueries(QVector<RawDatabase::Query>& upgradeQueries);
bool appendPopulateChatsQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
bool appendUpdateHistoryFkQueries(RawDatabase& db, QVector<RawDatabase::Query>& upgradeQueries);
void appendReplaceOldTablesQueries(QVector<RawDatabase::Query>& upgradeQueries);
void appendUpdateSystemMessagesFkQueries(QVector<RawDatabase::Query>& upgradeQueries);
void appendUpdateBrokenMessagesFkQueries(QVector<RawDatabase::Query>& upgradeQueries);
void appendUpdateFauxOfflinePendingFkQueries(QVector<RawDatabase::Query>& upgradeQueries);
} // namespace PeersToChats

void appendUpdateTextMessagesFkQueries(QVector<RawDatabase::Query>& upgradeQueries);
void appendUpdateFileTransfersFkQueries(QVector<RawDatabase::Query>& upgradeQueries);
void appendDropPeersQueries(QVector<RawDatabase::Query>& upgradeQueries);
} // namespace DbTo11
