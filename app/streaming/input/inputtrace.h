#pragma once

#include <QJsonArray>
#include <QString>
#include <QVector>

struct InputTraceEvent {
    enum class Type { AbsoluteMouse, RelativeMouse, Touchpad, Scroll, ControllerAxis };
    Type type;
    qint64 timestampUs;
    int deviceRateHz;
    double x;
    double y;
    int flags;
};

class InputTrace
{
public:
    static QJsonArray serialize(const QVector<InputTraceEvent>& events);
    static bool deserialize(const QJsonArray& json, QVector<InputTraceEvent>* events,
                            QString* error = nullptr);
};
