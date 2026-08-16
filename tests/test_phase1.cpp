#include <QtTest>

#include "backend/nvaddress.h"
#include "diagnostics/crashcontext.h"
#include "diagnostics/performancecounters.h"
#include "streaming/audio/audioqueuepolicy.h"
#include "streaming/input/inputtrace.h"
#include "streaming/streamlogic.h"
#include "streaming/video/framecontract.h"
#include "streaming/video/colorlogic.h"

class Phase1Tests : public QObject
{
    Q_OBJECT
private slots:
    void aspectFitAndNormalization();
    void bitrateSelection();
    void frameRateSelection();
    void colorSelection();
    void addressFormatting();
    void settingsMigration();
    void rendererOwnershipAndReset();
    void audioQueueFaults();
    void inputTraceReplayAndValidation();
    void sampledPerformanceCounters();
    void crashContextRedaction();
};

void Phase1Tests::aspectFitAndNormalization()
{
    QCOMPARE(StreamLogic::fitAspectRatio({0, 0, 1920, 1080}, {0, 0, 1024, 768}),
             (StreamLogic::IntRect{0, 96, 1024, 576}));
    QCOMPARE(StreamLogic::fitAspectRatio({0, 0, 4, 3}, {10, 20, 1920, 1080}),
             (StreamLogic::IntRect{250, 20, 1440, 1080}));
    const auto normalized = StreamLogic::normalizeRect({0, 0, 960, 540}, 1920, 1080);
    QCOMPARE(normalized.x, -1.0f);
    QCOMPARE(normalized.y, -1.0f);
    QCOMPARE(normalized.width, 1.0f);
    QCOMPARE(normalized.height, 1.0f);
    QCOMPARE(StreamLogic::normalizeRect({1, 2, 3, 4}, 0, 0).width, 0.0f);
}

void Phase1Tests::bitrateSelection()
{
    QCOMPARE(StreamLogic::defaultBitrateKbps(1280, 720, 60, false), 10000);
    QCOMPARE(StreamLogic::defaultBitrateKbps(3840, 2160, 60, false), 80000);
    QCOMPARE(StreamLogic::defaultBitrateKbps(3840, 2160, 60, true), 160000);
    QCOMPARE(StreamLogic::defaultBitrateKbps(1280, 720, 120, false), 14000);
}

void Phase1Tests::frameRateSelection()
{
    const std::vector<StreamLogic::DisplayMode> modes{{2560, 1664, 60},
        {2560, 1664, 120}, {1920, 1080, 120}, {1920, 1200, 120}};
    QCOMPARE(StreamLogic::selectDisplayMode(modes, {2560, 1664, 60},
                                            1920, 1080, 60, false).refreshRate, 120);
    const auto matched = StreamLogic::selectDisplayMode(modes, {2560, 1664, 60},
                                                         1920, 1080, 120, true);
    QCOMPARE(matched.width, 1920);
    QCOMPARE(matched.height, 1080);
    QCOMPARE(StreamLogic::selectDisplayMode(modes, {2560, 1664, 60},
                                            1920, 1080, 144, false).refreshRate, 60);
}

void Phase1Tests::colorSelection()
{
    using namespace FrameColorLogic;
    QCOMPARE(selectSpace(Space::Rec2020, Space::Rec709), Space::Rec2020);
    QCOMPARE(selectSpace(Space::Unspecified, Space::Rec709), Space::Rec709);
    QVERIFY(selectFullRange(Range::Full, false));
    QVERIFY(!selectFullRange(Range::Limited, true));
    QVERIFY(selectFullRange(Range::Unspecified, true));
}

void Phase1Tests::addressFormatting()
{
    QCOMPARE(NvAddress("192.0.2.1", 47989).toString(), QString("192.0.2.1:47989"));
    QCOMPARE(NvAddress("2001:db8::1", 47984).toString(), QString("[2001:db8::1]:47984"));
    QCOMPARE(NvAddress().toString(), QString("<NULL>"));
}

void Phase1Tests::settingsMigration()
{
    auto mac = StreamLogic::migrateSettings(0, true, false, {0, 3, false});
    QCOMPARE(mac.windowMode, 1);
    QCOMPARE(mac.videoCodec, 0);
    QVERIFY(mac.hdrEnabled);
    auto wayland = StreamLogic::migrateSettings(1, false, true, {0, 0, false});
    QCOMPARE(wayland.windowMode, 1);
    auto current = StreamLogic::migrateSettings(2, true, true, {0, 0, false});
    QCOMPARE(current.windowMode, 0);
}

void Phase1Tests::rendererOwnershipAndReset()
{
    LatestFrameMailbox<int> mailbox;
    QVERIFY(!mailbox.submit(1, mailbox.generation()));
    QCOMPARE(mailbox.submit(2, mailbox.generation()).value(), 1);
    QCOMPARE(mailbox.take().value(), 2);
    QVERIFY(!mailbox.take());
    QVERIFY(!mailbox.submit(3, mailbox.generation()));
    QCOMPARE(mailbox.reset().value(), 3);
    QCOMPARE(mailbox.submit(4, 0).value(), 4); // stale frame is returned to owner
    QVERIFY(!mailbox.take());
}

void Phase1Tests::audioQueueFaults()
{
    AudioQueuePolicy policy({20, 30, 50});
    QCOMPARE(policy.evaluate(10, 10, true, false), AudioQueuePolicy::Decision::Accept);
    QCOMPARE(policy.evaluate(60, 10, true, false), AudioQueuePolicy::Decision::DropIncoming);
    QCOMPARE(policy.evaluate(10, 60, true, false), AudioQueuePolicy::Decision::Backpressure);
    QCOMPARE(policy.evaluate(0, 0, false, false), AudioQueuePolicy::Decision::Reinitialize);
    QCOMPARE(policy.evaluate(0, 0, true, true), AudioQueuePolicy::Decision::Reinitialize);
}

void Phase1Tests::inputTraceReplayAndValidation()
{
    const QVector<InputTraceEvent> source{
        {InputTraceEvent::Type::AbsoluteMouse, 0, 125, 0.5, 0.5, 0},
        {InputTraceEvent::Type::RelativeMouse, 1000, 1000, 4, -2, 1},
        {InputTraceEvent::Type::Scroll, 2000, 500, 0, 0.25, 0},
        {InputTraceEvent::Type::ControllerAxis, 3000, 0, -1, 1, 2},
    };
    QVector<InputTraceEvent> replay;
    QString error;
    QVERIFY(InputTrace::deserialize(InputTrace::serialize(source), &replay, &error));
    QCOMPARE(replay.size(), source.size());
    QCOMPARE(replay[1].deviceRateHz, 1000);
    QCOMPARE(replay[2].y, 0.25);

    auto malformed = InputTrace::serialize(source);
    auto object = malformed[1].toObject();
    object["timestamp_us"] = -1;
    malformed[1] = object;
    QVERIFY(!InputTrace::deserialize(malformed, &replay, &error));
}

void Phase1Tests::sampledPerformanceCounters()
{
    auto& counters = PerformanceCounters::instance();
    counters.reset();
    counters.configure(true, 2);
    counters.record(PerformanceCounters::Metric::Decode, 100);
    counters.record(PerformanceCounters::Metric::Decode, 300);
    counters.incrementReplacedFrames();
    const auto snapshot = counters.snapshot();
    const auto decode = snapshot["metrics"].toObject()["decode"].toObject();
    QCOMPARE(decode["samples"].toInteger(), 1);
    QCOMPARE(decode["mean_us"].toDouble(), 300.0);
    QCOMPARE(snapshot["replaced_frames"].toInteger(), 1);
}

void Phase1Tests::crashContextRedaction()
{
    CrashContextInput input;
    input.appCommit = "abc123";
    input.architecture = "arm64";
    input.audioDevice = "Justin's AirPods /Users/justin";
    const auto output = CrashContext::sanitized(input);
    QVERIFY(!output.contains("host"));
    QVERIFY(!output.contains("address"));
    QVERIFY(!output.contains("path"));
    QVERIFY(output["audio_device_category"].toString() != input.audioDevice);
    QCOMPARE(output["audio_device_category"].toString().size(), 12);
}

QTEST_MAIN(Phase1Tests)
#include "test_phase1.moc"
