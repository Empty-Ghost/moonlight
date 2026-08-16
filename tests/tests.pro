QT += core network testlib
QT -= gui
CONFIG += console testcase c++17
CONFIG -= app_bundle
TEMPLATE = app
TARGET = moonlight-phase1-tests

INCLUDEPATH += ../app

SOURCES += \
    test_phase1.cpp \
    ../app/backend/nvaddress.cpp \
    ../app/diagnostics/crashcontext.cpp \
    ../app/diagnostics/performancecounters.cpp \
    ../app/streaming/audio/audioqueuepolicy.cpp \
    ../app/streaming/input/inputtrace.cpp \
    ../app/streaming/streamlogic.cpp

HEADERS += \
    ../app/backend/nvaddress.h \
    ../app/diagnostics/crashcontext.h \
    ../app/diagnostics/performancecounters.h \
    ../app/streaming/audio/audioqueuepolicy.h \
    ../app/streaming/input/inputtrace.h \
    ../app/streaming/streamlogic.h \
    ../app/streaming/video/colorlogic.h \
    ../app/streaming/video/framecontract.h

macx {
    QMAKE_APPLE_DEVICE_ARCHS = arm64
}
