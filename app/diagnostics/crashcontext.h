#pragma once

#include <QJsonObject>

struct CrashContextInput {
    QString appCommit;
    QString dependencyBundle;
    QString architecture;
    QString osBuild;
    QString machineIdentifier;
    QString renderer;
    QString codec;
    QString pixelFormat;
    int displayRefreshHz = 0;
    double displayScale = 0;
    QString audioDevice;
    QString powerState;
    QString thermalState;
};

class CrashContext
{
public:
    static QJsonObject sanitized(const CrashContextInput& input);
};
