/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2026 The TokTok team.
 */

#pragma once

#include <QDebug>
#include <QString>

#include <optional>

struct Version
{
    int major = 0;
    int minor = 0;
    int patch = 0;

    bool operator==(const Version& other) const
    {
        return major == other.major && minor == other.minor && patch == other.patch;
    }
};

QDebug& operator<<(QDebug& stream, const Version& version);

std::optional<Version> tagToVersion(const QString& tagName);

bool isUpdateAvailable(const Version& current, const Version& available);

bool isVersionStable(const QString& gitDescribeExact);
