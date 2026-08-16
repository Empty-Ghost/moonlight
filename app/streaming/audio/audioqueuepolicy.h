#pragma once

class AudioQueuePolicy
{
public:
    enum class Decision { Accept, DropIncoming, Backpressure, Reinitialize };

    struct Limits {
        int targetPendingMs = 20;
        int maximumProtocolPendingMs = 30;
        int maximumDevicePendingMs = 50;
    };

    AudioQueuePolicy();
    explicit AudioQueuePolicy(Limits limits);
    Decision evaluate(int protocolPendingMs, int devicePendingMs,
                      bool deviceAvailable, bool formatChanged) const;
    Limits limits() const { return m_Limits; }

private:
    Limits m_Limits;
};
