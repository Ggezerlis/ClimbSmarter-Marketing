import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Timeline (30 fps)
const FAIL_DUR = 151; // 5.04s  – V1 attempt + fall
const CARD_DUR = 45; //  1.5s  – "6 months later" beat card
const MID_DUR = 195; //  6.5s  – V10 steep section
const TOP_DUR = 256; //  8.55s – V10 finish + top-out
const END_DUR = 133; //  4.43s – CTA end card
export const REEL_DURATION =
  FAIL_DUR + CARD_DUR + MID_DUR + TOP_DUR + END_DUR; // 780 frames = 26s

const AMBIENCE = 0.14; // keep gym noise low under the VO

const font: React.CSSProperties = {
  fontFamily:
    "'Helvetica Neue', Helvetica, 'Segoe UI', Arial, sans-serif",
  fontWeight: 800,
  color: "white",
  textShadow: "0 2px 24px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.9)",
  textAlign: "center",
};

const TopText: React.FC<{ big: string; small?: string }> = ({
  big,
  small,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 14 } });
  return (
    <AbsoluteFill
      style={{ alignItems: "center", pointerEvents: "none" }}
    >
      <div
        style={{
          marginTop: 200,
          transform: `translateY(${(1 - s) * -60}px)`,
          opacity: s,
          ...font,
        }}
      >
        <div style={{ fontSize: 92, lineHeight: 1.05 }}>{big}</div>
        {small ? (
          <div style={{ fontSize: 44, fontWeight: 600, marginTop: 14 }}>
            {small}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const BeatCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 12 } });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0c0c0e",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          ...font,
          fontSize: 84,
          lineHeight: 1.2,
          maxWidth: 860,
          transform: `scale(${0.85 + 0.15 * s})`,
          opacity: s,
        }}
      >
        6 months of{" "}
        <span style={{ color: "#4ade80" }}>ClimbSmarter</span>
        <br />
        later…
      </div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inOp = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const s = spring({ frame: frame - 6, fps, config: { damping: 13 } });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0c0c0e",
        justifyContent: "center",
        alignItems: "center",
        opacity: inOp,
      }}
    >
      <div style={{ ...font, transform: `scale(${0.9 + 0.1 * s})` }}>
        <div style={{ fontSize: 110, letterSpacing: -2 }}>
          Climb<span style={{ color: "#4ade80" }}>Smarter</span>
        </div>
        <div style={{ fontSize: 46, fontWeight: 600, marginTop: 28 }}>
          Train smarter. Climb harder.
        </div>
        <div
          style={{
            fontSize: 38,
            fontWeight: 600,
            marginTop: 60,
            color: "#4ade80",
          }}
        >
          climbsmarter.app
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Badge: React.FC<{ label: string }> = ({ label }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 11 } });
  return (
    <div
      style={{
        position: "absolute",
        top: 200,
        right: 60,
        backgroundColor: "#4ade80",
        color: "#0c0c0e",
        fontFamily: font.fontFamily,
        fontWeight: 800,
        fontSize: 64,
        padding: "10px 34px",
        borderRadius: 18,
        transform: `scale(${s}) rotate(6deg)`,
      }}
    >
      {label}
    </div>
  );
};

export const Reel: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0c0c0e" }}>
      <Audio src={staticFile("vo.mp3")} />

      <Sequence durationInFrames={FAIL_DUR}>
        <OffthreadVideo
          src={staticFile("segments/fail.mp4")}
          volume={AMBIENCE}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
        <TopText big="me on a V1" small="(yes, really)" />
      </Sequence>

      <Sequence from={FAIL_DUR} durationInFrames={CARD_DUR}>
        <BeatCard />
      </Sequence>

      <Sequence from={FAIL_DUR + CARD_DUR} durationInFrames={MID_DUR}>
        <OffthreadVideo
          src={staticFile("segments/send_mid.mp4")}
          volume={AMBIENCE}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
        <Badge label="V10" />
      </Sequence>

      <Sequence
        from={FAIL_DUR + CARD_DUR + MID_DUR}
        durationInFrames={TOP_DUR}
      >
        <OffthreadVideo
          src={staticFile("segments/send_top.mp4")}
          volume={AMBIENCE}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </Sequence>

      <Sequence from={FAIL_DUR + CARD_DUR + MID_DUR + TOP_DUR}>
        <EndCard />
      </Sequence>
    </AbsoluteFill>
  );
};
