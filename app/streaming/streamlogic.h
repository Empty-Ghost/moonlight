#pragma once

#include <vector>

namespace StreamLogic {

struct IntRect {
    int x;
    int y;
    int width;
    int height;
};

inline bool operator==(const IntRect& left, const IntRect& right)
{
    return left.x == right.x && left.y == right.y &&
           left.width == right.width && left.height == right.height;
}

struct FloatRect {
    float x;
    float y;
    float width;
    float height;
};

struct DisplayMode {
    int width;
    int height;
    int refreshRate;
};

struct SettingsState {
    int windowMode;
    int videoCodec;
    bool hdrEnabled;
};

IntRect fitAspectRatio(IntRect source, IntRect destination);
FloatRect normalizeRect(IntRect rect, int viewportWidth, int viewportHeight);
int defaultBitrateKbps(int width, int height, int fps, bool yuv444);
DisplayMode selectDisplayMode(const std::vector<DisplayMode>& modes,
                              DisplayMode desktopMode,
                              int videoWidth,
                              int videoHeight,
                              int streamFps,
                              bool matchVideoResolution);
SettingsState migrateSettings(int defaultVersion, bool isDarwin, bool isWayland,
                              SettingsState state);

}
