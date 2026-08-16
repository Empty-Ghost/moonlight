#pragma once

namespace FrameColorLogic {

enum class Space { Unspecified, Rec601, Rec709, Rec2020 };
enum class Range { Unspecified, Limited, Full };

inline Space selectSpace(Space frame, Space requested)
{
    return frame == Space::Unspecified ? requested : frame;
}

inline bool selectFullRange(Range frame, bool requestedFullRange)
{
    if (frame == Range::Full) return true;
    if (frame == Range::Limited) return false;
    return requestedFullRange;
}

}
