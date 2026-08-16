#include "inputtrace.h"

#include <QJsonObject>

static QString typeName(InputTraceEvent::Type type)
{
    switch (type) {
    case InputTraceEvent::Type::AbsoluteMouse: return "absolute_mouse";
    case InputTraceEvent::Type::RelativeMouse: return "relative_mouse";
    case InputTraceEvent::Type::Touchpad: return "touchpad";
    case InputTraceEvent::Type::Scroll: return "scroll";
    case InputTraceEvent::Type::ControllerAxis: return "controller_axis";
    }
    return {};
}

static bool parseType(const QString& value, InputTraceEvent::Type* type)
{
    if (value == "absolute_mouse") *type = InputTraceEvent::Type::AbsoluteMouse;
    else if (value == "relative_mouse") *type = InputTraceEvent::Type::RelativeMouse;
    else if (value == "touchpad") *type = InputTraceEvent::Type::Touchpad;
    else if (value == "scroll") *type = InputTraceEvent::Type::Scroll;
    else if (value == "controller_axis") *type = InputTraceEvent::Type::ControllerAxis;
    else return false;
    return true;
}

QJsonArray InputTrace::serialize(const QVector<InputTraceEvent>& events)
{
    QJsonArray output;
    for (const auto& event : events) {
        output.append(QJsonObject{{"type", typeName(event.type)},
                                  {"timestamp_us", event.timestampUs},
                                  {"device_rate_hz", event.deviceRateHz},
                                  {"x", event.x}, {"y", event.y},
                                  {"flags", event.flags}});
    }
    return output;
}

bool InputTrace::deserialize(const QJsonArray& json, QVector<InputTraceEvent>* events,
                             QString* error)
{
    if (!events) return false;
    QVector<InputTraceEvent> parsed;
    qint64 previousTimestamp = -1;
    for (const auto& value : json) {
        const auto object = value.toObject();
        InputTraceEvent event{};
        if (!parseType(object.value("type").toString(), &event.type) ||
            !object.value("timestamp_us").isDouble() ||
            !object.value("device_rate_hz").isDouble() ||
            !object.value("x").isDouble() || !object.value("y").isDouble()) {
            if (error) *error = "Malformed input trace event";
            return false;
        }
        event.timestampUs = object.value("timestamp_us").toInteger();
        event.deviceRateHz = object.value("device_rate_hz").toInt();
        event.x = object.value("x").toDouble();
        event.y = object.value("y").toDouble();
        event.flags = object.value("flags").toInt();
        if (event.timestampUs < previousTimestamp || event.deviceRateHz < 0 ||
            event.deviceRateHz > 8000) {
            if (error) *error = "Invalid input trace ordering or device rate";
            return false;
        }
        previousTimestamp = event.timestampUs;
        parsed.append(event);
    }
    *events = parsed;
    return true;
}
