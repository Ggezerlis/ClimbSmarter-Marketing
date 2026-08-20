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
import captions from "./captions.json";

// ---------------------------------------------------------------------------
// The score runs at 120 BPM (bar = 2.0s), and every cut below lands on a beat.
// The fall is placed so it hits the impact on the bar at 2.0s.
// ---------------------------------------------------------------------------
export const FPS = 30;
const S = (sec: number) => Math.round(sec * FPS);

const SHOTS = [
  { at: 0.0, dur: 3.0, src: "v3/fail.mp4" },
  { at: 3.0, dur: 3.0, card: "beat" as const },
  { at: 6.0, dur: 3.0, src: "v3/onboarding.mp4", mute: true },
  { at: 9.0, dur: 4.0, src: "v3/plan.mp4", mute: true },
  { at: 13.0, dur: 4.0, src: "v3/progress.mp4", mute: true },
  { at: 17.0, dur: 3.0, src: "v3/bridge.mp4" },
  { at: 20.0, dur: 4.0, src: "v3/send_mid.mp4" },
  { at: 24.0, dur: 5.0, src: "v3/send_top.mp4" },
  { at: 29.0, dur: 3.0, card: "end" as const },
];

export const AD_DURATION = S(32);

/** Gym noise sits well under the score; the app screens are silent. */
const AMBIENCE = 0.07;

const base: React.CSSProperties = {
  fontFamily: FONT_STACK,
  fontWeight: 800,
  color: "white",
  textAlign: "center",
};

const Wordmark: React.FC<{ size: number }> = ({ size }) => (
  <span style={{ ...base, fontSize: size, letterSpacing: size * 0.005 }}>
    CLIMB<span style={{ color: BRAND.orange }}>SMARTER</span>
  </span>
);

/**
 * Karaoke captions. Most reels are watched muted, so this is the line that
 * actually has to carry the message.
 */
const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const now = frame / FPS;
  // The app animation (6s-17s) has its own on-screen captions.
  if (now >= 6 && now < 17) return null;
  const chunk = captions.find((c) => now >= c.start && now <= c.end);
  if (!chunk) return null;

  const pop = interpolate(now - chunk.start, [0, 0.12], [0.86, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", pointerEvents: "none" }}
    >
      <div
        style={{
          // clear of the Reels caption/CTA furniture along the bottom
          marginBottom: 430,
          maxWidth: 940,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 20px",
          transform: `scale(${pop})`,
        }}
      >
        {chunk.words.map((w, i) => {
          const live = now >= w.s - 0.02 && now <= w.e + 0.06;
          return (
            <span
              key={i}
              style={{
                ...base,
                fontSize: 86,
                lineHeight: 1.14,
                color: live ? BRAND.orange : "white",
                WebkitTextStroke: "3px rgba(0,0,0,0.85)",
                paintOrder: "stroke fill",
                textShadow: "0 6px 26px rgba(0,0,0,0.9)",
              }}
            >
              {w.t}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Hook title — on screen for the first beat only, then out of the way. */
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 13, mass: 0.6 } });
  const out = interpolate(frame, [S(1.6), S(2.0)], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ alignItems: "center", pointerEvents: "none" }}>
      <div
        style={{
          marginTop: 300,
          opacity: out,
          transform: `scale(${0.8 + 0.2 * s})`,
          ...base,
          fontSize: 132,
          lineHeight: 1,
          WebkitTextStroke: "4px rgba(0,0,0,0.8)",
          paintOrder: "stroke fill",
          textShadow: "0 8px 34px rgba(0,0,0,0.9)",
        }}
      >
        ME.
        <br />
        ON A <span style={{ color: BRAND.orange }}>V1</span>.
      </div>
    </AbsoluteFill>
  );
};

/** White flash on the fall and on the send — sells the impact. */
const Flash: React.FC<{ at: number; amp?: number }> = ({ at, amp = 0.75 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [S(at), S(at + 0.06), S(at + 0.4)], [0, amp, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ backgroundColor: "white", opacity: o }} />;
};

const BeatCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 12 } });
  return (
    <AbsoluteFill
      style={{ backgroundColor: BRAND.ink, justifyContent: "center", alignItems: "center" }}
    >
      <div style={{ ...base, fontSize: 96, lineHeight: 1.3, opacity: s }}>
        <span style={{ color: BRAND.muted, fontSize: 46, fontWeight: 700, letterSpacing: 6 }}>
          TWO YEARS OF GUESSING
        </span>
        <br />
        <br />
        So I tried
        <br />
        <Wordmark size={96} />
      </div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 3, fps, config: { damping: 13 } });
  const cta = spring({ frame: frame - S(1.3), fps, config: { damping: 14 } });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BRAND.ink,
        justifyContent: "center",
        alignItems: "center",
        opacity: interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" }),
      }}
    >
      <div style={{ ...base, transform: `scale(${0.93 + 0.07 * s})` }}>
        <Wordmark size={112} />
        <div style={{ fontSize: 62, fontWeight: 800, marginTop: 46, lineHeight: 1.22 }}>
          Stop guessing.
          <br />
          <span style={{ color: BRAND.orange }}>Start sending.</span>
        </div>
        <div
          style={{
            marginTop: 64,
            opacity: cta,
            transform: `translateY(${(1 - cta) * 26}px)`,
          }}
        >
          <div
            style={{
              ...base,
              display: "inline-block",
              fontSize: 44,
              backgroundColor: BRAND.orange,
              color: BRAND.ink,
              padding: "22px 56px",
              borderRadius: 999,
            }}
          >
            climbsmarter.app
          </div>
          <div style={{ ...base, fontSize: 30, fontWeight: 600, marginTop: 26, color: BRAND.muted }}>
            14 days free · no card
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Ad: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: BRAND.ink }}>
    {/* One pre-mixed track: original score + voiceover, ducked and limited. */}
    <Audio src={staticFile("v3/master.m4a")} />

    {SHOTS.map((s) => (
      <Sequence key={s.at} from={S(s.at)} durationInFrames={S(s.dur)}>
        {s.card === "beat" ? (
          <BeatCard />
        ) : s.card === "end" ? (
          <EndCard />
        ) : (
          <OffthreadVideo
            src={staticFile(s.src!)}
            volume={s.mute ? 0 : AMBIENCE}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </Sequence>
    ))}

    <Sequence durationInFrames={S(3)}>
      <Hook />
    </Sequence>

    <Flash at={2.0} amp={0.45} />
    <Flash at={20.0} amp={0.38} />

    <Captions />
  </AbsoluteFill>
);
