#include "streamlogic.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace StreamLogic {

IntRect fitAspectRatio(IntRect source, IntRect destination)
{
    if (source.width <= 0 || source.height <= 0 ||
        destination.width <= 0 || destination.height <= 0) {
        return destination;
    }

    const int fittedHeight = static_cast<int>(std::ceil(
        static_cast<double>(destination.width) * source.height / source.width));
    const int fittedWidth = static_cast<int>(std::ceil(
        static_cast<double>(destination.height) * source.width / source.height));

    if (fittedHeight > destination.height) {
        destination.x += (destination.width - fittedWidth) / 2;
        destination.width = fittedWidth;
    }
    else {
        destination.y += (destination.height - fittedHeight) / 2;
        destination.height = fittedHeight;
    }
    return destination;
}

FloatRect normalizeRect(IntRect rect, int viewportWidth, int viewportHeight)
{
    if (viewportWidth <= 0 || viewportHeight <= 0) {
        return {0, 0, 0, 0};
    }
    return {
        (rect.x / (viewportWidth / 2.0f)) - 1.0f,
        (rect.y / (viewportHeight / 2.0f)) - 1.0f,
        rect.width / (viewportWidth / 2.0f),
        rect.height / (viewportHeight / 2.0f),
    };
}

int defaultBitrateKbps(int width, int height, int fps, bool yuv444)
{
    const float frameRateFactor =
        (fps <= 60 ? fps : (std::sqrt(fps / 60.0f) * 60.0f)) / 30.0f;
    static constexpr struct { int pixels; int factor; } table[] = {
        {640 * 360, 1}, {854 * 480, 2}, {1280 * 720, 5},
        {1920 * 1080, 10}, {2560 * 1440, 20}, {3840 * 2160, 40},
    };

    const long long pixels = std::max(0LL, static_cast<long long>(width) * height);
    float resolutionFactor = table[0].factor;
    if (pixels >= table[5].pixels) {
        resolutionFactor = table[5].factor;
    }
    else {
        for (size_t i = 1; i < std::size(table); ++i) {
            if (pixels <= table[i].pixels) {
                const auto& low = table[i - 1];
                const auto& high = table[i];
                resolutionFactor = static_cast<float>(pixels - low.pixels) /
                    (high.pixels - low.pixels) * (high.factor - low.factor) + low.factor;
                break;
            }
        }
    }
    if (yuv444) {
        resolutionFactor *= 2;
    }
    return static_cast<int>(std::lround(resolutionFactor * frameRateFactor)) * 1000;
}

DisplayMode selectDisplayMode(const std::vector<DisplayMode>& modes,
                              DisplayMode desktopMode,
                              int videoWidth,
                              int videoHeight,
                              int streamFps,
                              bool matchVideoResolution)
{
    if (streamFps <= 0 || videoWidth <= 0 || videoHeight <= 0) {
        return desktopMode;
    }

    DisplayMode best{desktopMode.width, desktopMode.height, 0};
    if (!matchVideoResolution) {
        for (const auto& mode : modes) {
            if (mode.width == desktopMode.width && mode.height == desktopMode.height &&
                mode.refreshRate > 0 && mode.refreshRate % streamFps == 0 &&
                mode.refreshRate > best.refreshRate) {
                best = mode;
            }
        }
    }

    if (best.refreshRate == 0) {
        const double videoAspect = static_cast<double>(videoWidth) / videoHeight;
        double bestAspectDistance = std::numeric_limits<double>::max();
        for (const auto& mode : modes) {
            if (mode.width < videoWidth || mode.height < videoHeight ||
                mode.refreshRate <= 0 || mode.refreshRate % streamFps != 0) {
                continue;
            }
            const double distance = std::abs(videoAspect -
                static_cast<double>(mode.width) / mode.height);
            if (mode.refreshRate > best.refreshRate ||
                (mode.refreshRate == best.refreshRate && distance <= bestAspectDistance)) {
                best = mode;
                bestAspectDistance = distance;
            }
        }
    }
    return best.refreshRate == 0 ? desktopMode : best;
}

SettingsState migrateSettings(int defaultVersion, bool isDarwin, bool isWayland,
                              SettingsState state)
{
    constexpr int fullScreen = 0;
    constexpr int borderless = 1;
    constexpr int automaticCodec = 0;
    constexpr int deprecatedHevcHdrCodec = 3;
    if (defaultVersion < 1 && isDarwin && state.windowMode == fullScreen) {
        state.windowMode = borderless;
    }
    if (defaultVersion < 2 && isWayland && state.windowMode == fullScreen) {
        state.windowMode = borderless;
    }
    if (state.videoCodec == deprecatedHevcHdrCodec) {
        state.videoCodec = automaticCodec;
        state.hdrEnabled = true;
    }
    return state;
}

}
