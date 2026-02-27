/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2024-2026 The TokTok team.
 */

#pragma once

#include <QAbstractListModel>
#include <QLoggingCategory>

class DebugLogModel : public QAbstractListModel
{
    Q_OBJECT
public:
    enum Filter
    {
        All,
        Debug,
        Info,
        Warning,
        Critical,
        Fatal,
    };

    Q_ENUM(Filter)

    // [12:35:16.634 UTC] src/core/core.cpp:370 : Debug: Connected to a TCP relay
    struct LogEntry
    {
        /// Index in the original log list.
        int index{0};

        QString time;
        QString category;
        QString file;
        int line{0};
        QtMsgType type{QtDebugMsg};
        QString message;
    };

    explicit DebugLogModel(QObject* parent);
    ~DebugLogModel() override;

    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;

    void reload(const QStringList& newLogs);

    void setFilter(Filter filter);

    /**
     * @brief Given the index in the filtered list, return the index in the original list.
     */
    int originalIndex(const QModelIndex& index) const;

private:
    void recomputeFilter();

    Filter filter_ = All;
    QList<LogEntry> logs_;
    QList<LogEntry> filteredLogs_;
};
