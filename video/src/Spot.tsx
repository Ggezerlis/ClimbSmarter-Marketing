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

/**
 * One renderer for all five spots.
 *
 * Everything about a spot lives in a `SpotDef` - the picture edit, the burned-in
 * words, the highlight boxes - so a new cut is a data file, not a new component.
 * The audio is a single pre-mixed master built by src/audio/spots.py; both are
 * written against the same 120 BPM grid, so a shot at 6.0s and a music impact at
 * 6.0s land on the same frame.
 */

export const FPS = 30;
export const S = (sec: number) => Math.round(sec * FPS);

export type Shot = {
  at: number;
  dur: number;
  src: string;
  /** gym noise under the score; app screens are silent */
  gain?: number;
  /** slow push-in, [from, to] scale - keeps static UI from feeling like a JPEG */
  push?: [number, number];
  /** horizontal drift as a fraction of frame width, for tracking a climber */
  pan?: [number, number];
  rate?: number;
  /** start offset into the clip */
  from?: number;
};

/** Word-level timings from faster-whisper, so the caption tracks the read. */
export type Caption = {
  start: number;
  end: number;
  words: { t: string; s: number; e: number }[];
  /** lift the line above whatever UI is at the bottom of this shot */
  lift?: number;
};

/** Big statement text - the thing a muted viewer reads in the first second. */
export type TextBeat = {
  at: number;
  dur: number;
  text: string;
  kicker?: string;
  accent?: string;
  y?: "top" | "mid" | "low";
  size?: number;
};

/** Orange outline that snaps onto a piece of UI. Units are % of the frame. */
export type Focus = {
  at: number;
  dur: number;
  x: number;
  y: number;
  w: number;
  h: number;
  label?: string;
};

export type EndCard = {
  at: number;
  line1: string;
  line2?: string;
  kicker?: string;
  cta?: string;
  sub?: string;
  soft?: boolean;
};

export type SpotDef = {
  slug: string;
  seconds: number;
  master: string;
  shots: Shot[];
  captions: Caption[];
  beats?: TextBeat[];
  focus?: Focus[];
  flashes?: { at: number; amp: number }[];
  /** windows where the frame already carries the words */
  quiet?: [number, number][];
  end: EndCard;
};

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

// ---------------------------------------------------------------------------

const Clip: React.FC<{ shot: Shot }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const p = shot.dur > 0 ? frame / S(shot.dur) : 0;
  const scale = shot.push ? interpolate(p, [0, 1], shot.push) : 1;
  const dx = shot.pan ? interpolate(p, [0, 1], shot.pan) * 1080 : 0;
  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BRAND.ink }}>
      <OffthreadVideo
        src={staticFile(shot.src)}
        volume={shot.gain ?? 0}
        playbackRate={shot.rate}
        startFrom={shot.from ? S(shot.from) : undefined}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `translateX(${dx}px) scale(${scale})`,
        }}
      />
    </AbsoluteFill>
  );
};

/**
 * Karaoke captions. Reels are watched muted by default, so this line is doing
 * most of the work; the live word is orange and the rest stay white, because
 * orange-on-orange disappears over the app's own UI.
 */
const Captions: React.FC<{ spot: SpotDef }> = ({ spot }) => {
  const now = useCurrentFrame() / FPS;
  if (spot.quiet?.some(([a, b]) => now >= a && now < b)) return null;
  const chunk = spot.captions.find((c) => now >= c.start && now <= c.end);
  if (!chunk) return null;

  const pop = interpolate(now - chunk.start, [0, 0.12], [0.88, 1], {
    extrapolateRight: "clamp",
  });

  const lift = chunk.lift ?? 420;

  return (
    <AbsoluteFill
      style={{ justifyContent: "flex-end", alignItems: "center", pointerEvents: "none" }}
    >
      {/* Half of these captions land on top of the app's own text. A soft
          scrim keeps the line readable without hiding what is underneath. */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: lift - 150,
          height: 400,
          background:
            "linear-gradient(to bottom, rgba(10,10,11,0) 0%, rgba(10,10,11,0.5) 42%," +
            " rgba(10,10,11,0.5) 64%, rgba(10,10,11,0) 100%)",
        }}
      />
      <div
        style={{
          marginBottom: lift,
          maxWidth: 950,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 18px",
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
                fontSize: 78,
                lineHeight: 1.16,
                color: live ? BRAND.orange : "white",
                WebkitTextStroke: "3px rgba(0,0,0,0.85)",
                paintOrder: "stroke fill",
                textShadow: "0 6px 26px rgba(0,0,0,0.95)",
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

const Beat: React.FC<{ beat: TextBeat }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 14, mass: 0.55 } });
  const out = interpolate(
    frame,
    [S(beat.dur) - 7, S(beat.dur)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const justify =
    beat.y === "top" ? "flex-start" : beat.y === "low" ? "flex-end" : "center";
  return (
    <AbsoluteFill
      style={{
        justifyContent: justify,
        alignItems: "center",
        pointerEvents: "none",
        padding: beat.y === "top" ? "300px 60px 0" : beat.y === "low" ? "0 60px 520px" : "0 60px",
      }}
    >
      <div style={{ opacity: out, transform: `scale(${0.86 + 0.14 * s})` }}>
        {beat.kicker && (
          <div
            style={{
              ...base,
              fontSize: 38,
              fontWeight: 700,
              letterSpacing: 7,
              // white rather than orange: the statement under it is usually
              // orange too, and orange over orange reads as one block
              color: "rgba(255,255,255,0.86)",
              marginBottom: 42,
              textShadow: "0 4px 20px rgba(0,0,0,0.95)",
            }}
          >
            {beat.kicker}
          </div>
        )}
        <div
          style={{
            ...base,
            fontSize: beat.size ?? 108,
            lineHeight: 1.06,
            // the beats are written with their own line breaks
            whiteSpace: "pre-line",
            WebkitTextStroke: "4px rgba(0,0,0,0.8)",
            paintOrder: "stroke fill",
            textShadow: "0 8px 34px rgba(0,0,0,0.92)",
          }}
        >
          {beat.text.split("*").map((part, i) =>
            i % 2 ? (
              <span key={i} style={{ color: beat.accent ?? BRAND.orange }}>
                {part}
              </span>
            ) : (
              <span key={i}>{part}</span>
            ),
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Snaps an outline onto a control so the eye knows where to look. */
const FocusBox: React.FC<{ f: Focus }> = ({ f }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 16, stiffness: 140 } });
  const out = interpolate(frame, [S(f.dur) - 6, S(f.dur)], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: out }}>
      <div
        style={{
          position: "absolute",
          left: `${f.x}%`,
          top: `${f.y}%`,
          width: `${f.w}%`,
          height: `${f.h}%`,
          border: `6px solid ${BRAND.orange}`,
          borderRadius: 26,
          boxShadow: `0 0 0 8px rgba(249,115,22,0.16), 0 0 60px rgba(249,115,22,0.55)`,
          transform: `scale(${1.06 - 0.06 * s})`,
          opacity: s,
        }}
      />
      {f.label && (
        <div
          style={{
            position: "absolute",
            left: `${f.x}%`,
            top: `calc(${f.y}% - 74px)`,
            ...base,
            fontSize: 40,
            fontWeight: 800,
            color: BRAND.ink,
            backgroundColor: BRAND.orange,
            padding: "12px 26px",
            borderRadius: 999,
            opacity: s,
            transform: `translateY(${(1 - s) * 14}px)`,
          }}
        >
          {f.label}
        </div>
      )}
    </AbsoluteFill>
  );
};

const Flash: React.FC<{ at: number; amp: number }> = ({ at, amp }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [S(at), S(at + 0.05), S(at + 0.34)], [0, amp, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ backgroundColor: "white", opacity: o }} />;
};

const End: React.FC<{ card: EndCard }> = ({ card }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 2, fps, config: { damping: 14 } });
  const cta = spring({ frame: frame - S(0.7), fps, config: { damping: 15 } });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BRAND.ink,
        // a soft brand glow behind the wordmark, so the card is not a flat slab
        backgroundImage:
          "radial-gradient(120% 55% at 50% 46%, rgba(249,115,22,0.22), rgba(10,10,11,0) 68%)",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 70px",
        opacity: interpolate(frame, [0, 7], [0, 1], { extrapolateRight: "clamp" }),
      }}
    >
      <div style={{ ...base, transform: `scale(${0.94 + 0.06 * s})` }}>
        {card.kicker && (
          <div
            style={{
              ...base,
              fontSize: 34,
              fontWeight: 700,
              letterSpacing: 6,
              color: BRAND.muted,
              marginBottom: 30,
            }}
          >
            {card.kicker}
          </div>
        )}
        <div style={{ fontSize: card.soft ? 60 : 66, fontWeight: 800, lineHeight: 1.2 }}>
          {card.line1}
          {card.line2 && (
            <>
              <br />
              <span style={{ color: BRAND.orange }}>{card.line2}</span>
            </>
          )}
        </div>
        <div style={{ marginTop: 56 }}>
          <Wordmark size={96} />
        </div>
        <div
          style={{
            marginTop: 54,
            opacity: cta,
            transform: `translateY(${(1 - cta) * 24}px)`,
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
            {card.cta ?? "climbsmarter.app"}
          </div>
          {card.sub && (
            <div
              style={{ ...base, fontSize: 30, fontWeight: 600, marginTop: 26, color: BRAND.muted }}
            >
              {card.sub}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Spot: React.FC<{ spot: SpotDef }> = ({ spot }) => (
  <AbsoluteFill style={{ backgroundColor: BRAND.ink }}>
    <Audio src={staticFile(spot.master)} />

    {spot.shots.map((s) => (
      <Sequence key={`${s.at}-${s.src}`} from={S(s.at)} durationInFrames={S(s.dur)}>
        <Clip shot={s} />
      </Sequence>
    ))}

    <Sequence from={S(spot.end.at)} durationInFrames={S(spot.seconds - spot.end.at)}>
      <End card={spot.end} />
    </Sequence>

    {(spot.focus ?? []).map((f, i) => (
      <Sequence key={i} from={S(f.at)} durationInFrames={S(f.dur)}>
        <FocusBox f={f} />
      </Sequence>
    ))}

    {(spot.beats ?? []).map((b, i) => (
      <Sequence key={i} from={S(b.at)} durationInFrames={S(b.dur)}>
        <Beat beat={b} />
      </Sequence>
    ))}

    {(spot.flashes ?? []).map((f) => (
      <Flash key={f.at} at={f.at} amp={f.amp} />
    ))}

    <Captions spot={spot} />
  </AbsoluteFill>
);
