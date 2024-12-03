/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2014-2019 by The qTox Project Contributors
 * Copyright © 2024 The TokTok team.
 */

#pragma once

#include <QNetworkAccessManager>
#include <QObject>
#include <QTimer>
#include <QUrl>

class Settings;
class QString;
class QUrl;
class QNetworkReply;

class UpdateCheck : public QObject
{
    Q_OBJECT

public:
    explicit UpdateCheck(const Settings& settings_);

#ifdef UPDATE_CHECK_ENABLED
    void checkForUpdate();

signals:
    void updateAvailable(QString latestVersion, QUrl link);
    void upToDate();
    void updateCheckFailed();
    void versionIsUnstable();

private slots:
    void handleResponse(QNetworkReply* reply);

private:
    QNetworkAccessManager manager;
    QTimer updateTimer;
    const Settings& settings;
#endif
};
