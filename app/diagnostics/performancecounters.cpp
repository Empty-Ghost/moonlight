#include "performancecounters.h"

#include <QJsonArray>

#include <chrono>

static std::uint64_t monotonicMicroseconds()
{
    return std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}

PerformanceCounters& PerformanceCounters::instance()
{
    static PerformanceCounters counters;
    return counters;
}

QString PerformanceCounters::metricName(Metric metric)
{
    static const char* names[] = {"decode", "decoded_queue", "render_encode",
        "gpu_completion", "present", "input_dispatch", "audio_pending",
        "sdl_queue", "network_jitter"};
    return names[static_cast<size_t>(metric)];
}

void PerformanceCounters::configure(bool enabled, unsigned sampleEvery)
{
    m_Enabled.store(enabled, std::memory_order_relaxed);
    m_SampleEvery.store(sampleEvery == 0 ? 1 : sampleEvery, std::memory_order_relaxed);
}

void PerformanceCounters::record(Metric metric, std::uint64_t microseconds)
{
    if (!m_Enabled.load(std::memory_order_relaxed)) return;
    auto& counter = m_Counters[static_cast<size_t>(metric)];
    const auto index = counter.samples.fetch_add(1, std::memory_order_relaxed) + 1;
    if (index % m_SampleEvery.load(std::memory_order_relaxed) != 0) return;
    counter.totalUs.fetch_add(microseconds, std::memory_order_relaxed);
    auto maximum = counter.maximumUs.load(std::memory_order_relaxed);
    while (maximum < microseconds &&
           !counter.maximumUs.compare_exchange_weak(maximum, microseconds,
                                                    std::memory_order_relaxed)) {}
}

void PerformanceCounters::incrementReplacedFrames()
{
    if (m_Enabled.load(std::memory_order_relaxed))
        m_ReplacedFrames.fetch_add(1, std::memory_order_relaxed);
}

QJsonObject PerformanceCounters::snapshot() const
{
    QJsonObject metrics;
    const auto sampleEvery = m_SampleEvery.load(std::memory_order_relaxed);
    for (size_t i = 0; i < m_Counters.size(); ++i) {
        const auto attempts = m_Counters[i].samples.load(std::memory_order_relaxed);
        const auto samples = attempts / sampleEvery;
        const auto total = m_Counters[i].totalUs.load(std::memory_order_relaxed);
        metrics.insert(metricName(static_cast<Metric>(i)), QJsonObject{
            {"samples", static_cast<qint64>(samples)},
            {"mean_us", samples ? static_cast<double>(total) / samples : 0.0},
            {"max_us", static_cast<qint64>(m_Counters[i].maximumUs.load(std::memory_order_relaxed))},
        });
    }
    return QJsonObject{{"enabled", m_Enabled.load(std::memory_order_relaxed)},
                       {"sample_every", static_cast<int>(sampleEvery)},
                       {"replaced_frames", static_cast<qint64>(m_ReplacedFrames.load(std::memory_order_relaxed))},
                       {"metrics", metrics}};
}

void PerformanceCounters::reset()
{
    for (auto& counter : m_Counters) {
        counter.samples.store(0, std::memory_order_relaxed);
        counter.totalUs.store(0, std::memory_order_relaxed);
        counter.maximumUs.store(0, std::memory_order_relaxed);
    }
    m_ReplacedFrames.store(0, std::memory_order_relaxed);
}

ScopedPerformanceSample::ScopedPerformanceSample(PerformanceCounters::Metric metric)
    : m_Metric(metric),
      m_StartedUs(monotonicMicroseconds())
{
}

ScopedPerformanceSample::~ScopedPerformanceSample()
{
    const auto now = monotonicMicroseconds();
    PerformanceCounters::instance().record(m_Metric, now - m_StartedUs);
}
