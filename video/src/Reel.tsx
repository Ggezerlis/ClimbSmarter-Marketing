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
import { BRAND, FONT_STACK } from "./theme";

// ---------------------------------------------------------------------------
// Timeline (30 fps). Voiceover is cut into three lines so narration lands on
// the shot it describes: A over the V1 fail, B across the app walkthrough,
// C over the V10 top-out.
// ---------------------------------------------------------------------------
const FAIL = 151; // 5.03s  V1 attempt + fall            <- VO A (3.67s)
const CARD = 36; //  1.20s  "6 months later" beat
const APP1 = 90; //  3.00s  app: tell it your grade/goal <- VO B (11.04s)
const APP2 = 120; // 4.00s  app: today's session
const BRIDGE = 60; // 2.00s  training b-roll
const APP3 = 105; // 3.50s  app: progress + coach note
const MID = 120; //  4.00s  V10 steep section
const TOP = 180; //  6.00s  V10 finish + top-out         <- VO C (5.50s)
const END = 105; //  3.50s  CTA

const AT_CARD = FAIL;
const AT_APP1 = AT_CARD + CARD;
const AT_APP2 = AT_APP1 + APP1;
const AT_BRIDGE = AT_APP2 + APP2;
const AT_APP3 = AT_BRIDGE + BRIDGE;
const AT_MID = AT_APP3 + APP3;
const AT_TOP = AT_MID + MID;
const AT_END = AT_TOP + TOP;

export const REEL_DURATION = AT_END + END; // 967 frames = 32.2s

const AMBIENCE = 0.12; // gym noise sits under the voiceover

const heading: React.CSSProperties = {
  fontFamily: FONT_STACK,
  fontWeight: 800,
  color: "white",
  textShadow: "0 2px 24px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.9)",
  textAlign: "center",
};

const Clip: React.FC<{ src: string }> = ({ src }) => (
  <OffthreadVideo
    src={staticFile(src)}
    volume={AMBIENCE}
    style={{ width: "100%", height: "100%", objectFit: "cover" }}
  />
);

/** Caption pinned near the top, clear of the Reels UI. */
const TopText: React.FC<{ big: string; small?: string }> = ({ big, small }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 14 } });
  return (
    <AbsoluteFill style={{ alignItems: "center", pointerEvents: "none" }}>
      <div
        style={{
          marginTop: 210,
          transform: `translateY(${(1 - s) * -60}px)`,
          opacity: s,
          ...heading,
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

const Wordmark: React.FC<{ size: number }> = ({ size }) => (
  <span
    style={{
      fontFamily: FONT_STACK,
      fontWeight: 800,
      fontSize: size,
      letterSpacing: size * 0.01,
      color: "white",
    }}
  >
    CLIMB<span style={{ color: BRAND.orange }}>SMARTER</span>
  </span>
);

const BeatCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 12 } });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BRAND.ink,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          ...heading,
          fontSize: 84,
          lineHeight: 1.25,
          transform: `scale(${0.88 + 0.12 * s})`,
          opacity: s,
        }}
      >
        6 months of
        <br />
        <Wordmark size={84} />
        <br />
        later…
      </div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inOp = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: "clamp",
  });
  const s = spring({ frame: frame - 5, fps, config: { damping: 13 } });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BRAND.ink,
        justifyContent: "center",
        alignItems: "center",
        opacity: inOp,
      }}
    >
      <div style={{ ...heading, transform: `scale(${0.92 + 0.08 * s})` }}>
        <Wordmark size={104} />
        <div
          style={{
            fontSize: 58,
            fontWeight: 800,
            marginTop: 44,
            lineHeight: 1.2,
          }}
        >
          Stop guessing.
          <br />
          <span style={{ color: BRAND.orange }}>Start sending.</span>
        </div>
        <div
          style={{
            fontSize: 40,
            fontWeight: 600,
            marginTop: 56,
            color: BRAND.muted,
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
        top: 210,
        right: 64,
        backgroundColor: BRAND.orange,
        color: BRAND.ink,
        fontFamily: FONT_STACK,
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

export const Reel: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: BRAND.ink }}>
    <Sequence from={6}>
      <Audio src={staticFile("vo_a.mp3")} />
    </Sequence>
    <Sequence from={AT_APP1}>
      <Audio src={staticFile("vo_b.mp3")} />
    </Sequence>
    <Sequence from={AT_TOP + 12}>
      <Audio src={staticFile("vo_c.mp3")} />
    </Sequence>

    <Sequence durationInFrames={FAIL}>
      <Clip src="segments/fail.mp4" />
      <TopText big="me on a V1" small="(yes, really)" />
    </Sequence>

    <Sequence from={AT_CARD} durationInFrames={CARD}>
      <BeatCard />
    </Sequence>

    {/* The Replit-generated app animation carries its own captions and
        wordmark, so these scenes need no overlay of ours. */}
    <Sequence from={AT_APP1} durationInFrames={APP1}>
      <Clip src="app/onboarding.mp4" />
    </Sequence>

    <Sequence from={AT_APP2} durationInFrames={APP2}>
      <Clip src="app/plan.mp4" />
    </Sequence>

    <Sequence from={AT_BRIDGE} durationInFrames={BRIDGE}>
      <Clip src="segments/bridge.mp4" />
    </Sequence>

    <Sequence from={AT_APP3} durationInFrames={APP3}>
      <Clip src="app/progress.mp4" />
    </Sequence>

    <Sequence from={AT_MID} durationInFrames={MID}>
      <Clip src="segments/send_mid.mp4" />
      <Badge label="V10" />
    </Sequence>

    <Sequence from={AT_TOP} durationInFrames={TOP}>
      <Clip src="segments/send_top.mp4" />
    </Sequence>

    <Sequence from={AT_END}>
      <EndCard />
    </Sequence>
  </AbsoluteFill>
);
