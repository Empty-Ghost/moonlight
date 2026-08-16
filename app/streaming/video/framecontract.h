#pragma once

#include <cstdint>
#include <optional>
#include <utility>

// Single-slot latest-frame contract. A generation change invalidates frames
// owned by the renderer before a reset or color-space transition.
template<typename Frame>
class LatestFrameMailbox
{
public:
    struct Submission {
        Frame frame;
        std::uint64_t generation;
    };

    std::optional<Frame> submit(Frame frame, std::uint64_t generation)
    {
        if (generation != m_Generation) {
            return frame;
        }
        std::optional<Frame> replaced;
        if (m_Pending) {
            replaced = std::move(m_Pending->frame);
        }
        m_Pending = Submission{std::move(frame), generation};
        return replaced;
    }

    std::optional<Frame> take()
    {
        if (!m_Pending || m_Pending->generation != m_Generation) {
            m_Pending.reset();
            return std::nullopt;
        }
        auto frame = std::move(m_Pending->frame);
        m_Pending.reset();
        return frame;
    }

    std::optional<Frame> reset()
    {
        ++m_Generation;
        std::optional<Frame> released;
        if (m_Pending) {
            released = std::move(m_Pending->frame);
            m_Pending.reset();
        }
        return released;
    }

    std::uint64_t generation() const { return m_Generation; }

private:
    std::uint64_t m_Generation = 0;
    std::optional<Submission> m_Pending;
};
