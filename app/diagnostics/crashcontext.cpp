#include "crashcontext.h"

#include <QCryptographicHash>

static QString stableCategory(const QString& value)
{
    if (value.isEmpty()) return {};
    return QString::fromLatin1(QCryptographicHash::hash(value.toUtf8(),
                                QCryptographicHash::Sha256).toHex().left(12));
}

QJsonObject CrashContext::sanitized(const CrashContextInput& input)
{
    // User-selected device names may include a person's name. Preserve only a
    // stable category token; never accept host names, addresses, paths, or URLs.
    return QJsonObject{
        {"app_commit", input.appCommit},
        {"dependency_bundle", input.dependencyBundle},
        {"architecture", input.architecture},
        {"os_build", input.osBuild},
        {"machine_identifier", input.machineIdentifier},
        {"renderer", input.renderer}, {"codec", input.codec},
        {"pixel_format", input.pixelFormat},
        {"display_refresh_hz", input.displayRefreshHz},
        {"display_scale", input.displayScale},
        {"audio_device_category", stableCategory(input.audioDevice)},
        {"power_state", input.powerState}, {"thermal_state", input.thermalState},
    };
}
