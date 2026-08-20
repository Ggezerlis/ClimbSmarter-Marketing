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
import captions32 from "./captions.json";
import captions15 from "./captions15.json";

// ---------------------------------------------------------------------------
// The score runs at 120 BPM (bar = 2.0s), and every cut below lands on a beat.
// The fall is placed so it hits the impact on the bar at 2.0s.
// ---------------------------------------------------------------------------
export const FPS = 30;
const S = (sec: number) => Math.round(sec * FPS);

type Shot = {
  at: number;
  dur: number;
  src?: string;
  card?: "beat" | "end";
  mute?: boolean;
};

type Caption = {
  start: number;
  end: number;
  words: { t: string; s: number; e: number }[];
};

export type Cut = {
  shots: Shot[];
  captions: Caption[];
  seconds: number;
  /** windows where the frame already carries the words (app UI, end card) */
  quiet?: [number, number][];
  flashes: { at: number; amp: number }[];
};

const SHOTS: Shot[] = [
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
const Captions: React.FC<{ cut: Cut }> = ({ cut }) => {
  const frame = useCurrentFrame();
  const now = frame / FPS;
  // Where the app animation carries its own on-screen copy, ours would double it.
  if (cut.quiet?.some(([a, b]) => now >= a && now < b)) return null;
  const chunk = cut.captions.find((c) => now >= c.start && now <= c.end);
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

const EndCard: React.FC<{ ctaAt?: number }> = ({ ctaAt = 1.3 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 3, fps, config: { damping: 13 } });
  const cta = spring({ frame: frame - S(ctaAt), fps, config: { damping: 14 } });
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

const AdBase: React.FC<{ cut: Cut; master: string }> = ({ cut, master }) => (
  <AbsoluteFill style={{ backgroundColor: BRAND.ink }}>
    {/* One pre-mixed track: original score + voiceover, ducked and limited. */}
    <Audio src={staticFile(master)} />

    {cut.shots.map((s) => (
      <Sequence key={s.at} from={S(s.at)} durationInFrames={S(s.dur)}>
        {s.card === "beat" ? (
          <BeatCard />
        ) : s.card === "end" ? (
          <EndCard ctaAt={cut.seconds <= 20 ? 0.55 : 1.3} />
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

    {cut.flashes.map((f) => (
      <Flash key={f.at} at={f.at} amp={f.amp} />
    ))}

    <Captions cut={cut} />
  </AbsoluteFill>
);

/** 32s organic cut — tells the whole story. */
export const CUT_32: Cut = {
  shots: SHOTS,
  captions: captions32,
  seconds: 32,
  quiet: [[6, 17], [29, 32]],
  flashes: [{ at: 2.0, amp: 0.45 }, { at: 20.0, amp: 0.38 }],
};

/** 15s paid cut — same beat grid, half the bars, no app walkthrough to sit through. */
export const CUT_15: Cut = {
  shots: [
    { at: 0.0, dur: 2.5, src: "v15/fail.mp4" },
    { at: 2.5, dur: 1.5, card: "beat" },
    { at: 4.0, dur: 2.0, src: "v15/plan.mp4", mute: true },
    { at: 6.0, dur: 2.0, src: "v15/progress.mp4", mute: true },
    { at: 8.0, dur: 2.0, src: "v15/send_mid.mp4" },
    { at: 10.0, dur: 2.5, src: "v15/send_top.mp4" },
    { at: 12.5, dur: 2.5, card: "end" },
  ],
  captions: captions15,
  seconds: 15,
  quiet: [[12.5, 15]],
  flashes: [{ at: 2.0, amp: 0.45 }, { at: 8.0, amp: 0.38 }],
};

export const AD_DURATION = S(CUT_32.seconds);
export const AD15_DURATION = S(CUT_15.seconds);

export const Ad: React.FC = () => <AdBase cut={CUT_32} master="v3/master.mp3" />;
export const Ad15: React.FC = () => <AdBase cut={CUT_15} master="v15/master.mp3" />;
