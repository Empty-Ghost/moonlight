#include "audioqueuepolicy.h"

#include <algorithm>

AudioQueuePolicy::AudioQueuePolicy()
    : AudioQueuePolicy(Limits{})
{
}

AudioQueuePolicy::AudioQueuePolicy(Limits limits)
{
    m_Limits.targetPendingMs = std::clamp(limits.targetPendingMs, 5, 40);
    m_Limits.maximumProtocolPendingMs = std::clamp(limits.maximumProtocolPendingMs,
                                                   m_Limits.targetPendingMs + 5, 100);
    m_Limits.maximumDevicePendingMs = std::clamp(limits.maximumDevicePendingMs,
                                                 m_Limits.targetPendingMs + 5, 100);
}

AudioQueuePolicy::Decision AudioQueuePolicy::evaluate(int protocolPendingMs,
                                                       int devicePendingMs,
                                                       bool deviceAvailable,
                                                       bool formatChanged) const
{
    if (!deviceAvailable || formatChanged) {
        return Decision::Reinitialize;
    }
    if (protocolPendingMs > m_Limits.maximumProtocolPendingMs) {
        return Decision::DropIncoming;
    }
    if (devicePendingMs > m_Limits.maximumDevicePendingMs) {
        return Decision::Backpressure;
    }
    return Decision::Accept;
}
