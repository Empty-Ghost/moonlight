TEMPLATE = subdirs

macx {
    isEmpty(QMAKE_APPLE_DEVICE_ARCHS) {
        QMAKE_APPLE_DEVICE_ARCHS = arm64
    }
    !equals(QMAKE_APPLE_DEVICE_ARCHS, arm64) {
        error("Moonlight for macOS supports arm64 only")
    }
}

SUBDIRS = \
    moonlight-common-c \
    qmdnsengine \
    app \
    h264bitstream

# Build the dependencies in parallel before the final app
app.depends = qmdnsengine moonlight-common-c h264bitstream
win32:!winrt {
    SUBDIRS += AntiHooking
    app.depends += AntiHooking
}

# Support debug and release builds from command line for CI
CONFIG += debug_and_release

# Run our compile tests
load(configure)
qtCompileTest(SL)
qtCompileTest(EGL)
