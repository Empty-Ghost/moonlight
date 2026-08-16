#pragma once

#include <QJsonObject>
#include <QString>

#include <array>
#include <atomic>
#include <cstdint>

class PerformanceCounters
{
public:
    enum class Metric {
        Decode, DecodedQueue, RenderEncode, GpuCompletion, Present,
        InputDispatch, AudioPending, SdlQueue, NetworkJitter, Count
    };

    static PerformanceCounters& instance();
    static QString metricName(Metric metric);

    void configure(bool enabled, unsigned sampleEvery = 1);
    void record(Metric metric, std::uint64_t microseconds);
    void incrementReplacedFrames();
    QJsonObject snapshot() const;
    void reset();

private:
    struct Counter {
        std::atomic<std::uint64_t> samples{0};
        std::atomic<std::uint64_t> totalUs{0};
        std::atomic<std::uint64_t> maximumUs{0};
    };
    std::array<Counter, static_cast<size_t>(Metric::Count)> m_Counters;
    std::atomic<std::uint64_t> m_ReplacedFrames{0};
    std::atomic<unsigned> m_SampleEvery{1};
    std::atomic<bool> m_Enabled{false};
};

class ScopedPerformanceSample
{
public:
    explicit ScopedPerformanceSample(PerformanceCounters::Metric metric);
    ~ScopedPerformanceSample();
private:
    PerformanceCounters::Metric m_Metric;
    std::uint64_t m_StartedUs;
};
