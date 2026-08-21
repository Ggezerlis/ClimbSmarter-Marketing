import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { BRAND, FONT_STACK } from "./theme";

/**
 * The four-second diagram that sits in the middle of the Quiet Feet tip.
 *
 * It answers the one thing the macro footage cannot show: *why* a quiet
 * placement holds. Stomping loads the hold along a vector that pushes you off
 * it and puts a sliver of rubber down; placing the toe once loads into the wall
 * with the whole patch. Two halves, same shoe, same hold, so the only things
 * the eye has to compare are the arrow and the orange bar.
 *
 * Drawn here rather than fetched, so it carries the ads' own type and palette
 * and its timings land on the same 120 BPM grid as everything else.
 */

const RED = "#EF4444";
const HALF_H = 960;

const WALL_X = 150;
const WALL_W = 140;
const HOLD_X = WALL_X + WALL_W;   // the hold grows out of the wall face
const HOLD_TIP = 560;
const HOLD_BOTTOM = 700;
const LEDGE_Y = 480;              // the standing surface

const TOE_X = 300;                // where the toe ends up once it is on

const label: React.CSSProperties = {
  fontFamily: FONT_STACK,
  fontWeight: 800,
  fill: "white",
};

/**
 * Climbing shoe in profile, toe to the left, drawn so its sole is the line
 * y = 0 and its toe tip is x = 0 - which makes "standing on the hold" just
 * translate(TOE_X, LEDGE_Y). It is 340 x 150 at rest.
 */
const Shoe: React.FC<{ x: number; y: number; rot: number }> = ({ x, y, rot }) => (
  <g transform={`translate(${x} ${y}) rotate(${rot})`}>
    <path
      d={`M 150 -150 L 340 -104 L 335 -${HALF_H} L 175 -${HALF_H} Z`}
      fill="#2E2E38"
    />
    <path
      d={`M 0 -26
          C 4 -10, 16 0, 40 0
          L 300 0
          C 330 0, 340 -18, 340 -46
          L 340 -104
          L 150 -150
          C 96 -150, 40 -110, 0 -26 Z`}
      fill="#55555F"
      stroke="#9A9AAA"
      strokeWidth={5}
    />
    {/* rubber: the part that actually touches anything */}
    <path
      d={`M 0 -26 C 4 -10, 16 0, 40 0 L 300 0 L 300 -24 L 40 -24
          C 20 -24, 8 -26, 0 -26 Z`}
      fill="#1C1C22"
    />
  </g>
);

const Wall: React.FC = () => (
  <>
    <rect x={WALL_X} y={0} width={WALL_W} height={HALF_H} fill="#3F3F4B" />
    <rect x={WALL_X + WALL_W - 6} y={0} width={6} height={HALF_H} fill="#54545F" />
    {/* flat-topped foothold; the top edge is the standing surface */}
    <path
      d={`M ${HOLD_X} ${LEDGE_Y} L ${HOLD_TIP} ${LEDGE_Y} L ${HOLD_X} ${HOLD_BOTTOM} Z`}
      fill="#75758A"
    />
  </>
);

const Arrow: React.FC<{ x: number; y: number; dx: number; dy: number; color: string }> = ({
  x, y, dx, dy, color,
}) => {
  const len = Math.hypot(dx, dy);
  const a = (Math.atan2(dy, dx) * 180) / Math.PI;
  return (
    <g transform={`translate(${x} ${y}) rotate(${a})`}>
      <rect x={0} y={-9} width={Math.max(len - 48, 0)} height={18} rx={9} fill={color} />
      <path d={`M ${len} 0 L ${len - 52} -34 L ${len - 52} 34 Z`} fill={color} />
    </g>
  );
};

const Spark: React.FC<{ o: number }> = ({ o }) => (
  <g opacity={o} transform={`translate(${TOE_X + 30} ${LEDGE_Y - 10})`}>
    {[-58, -14, 30].map((a, i) => (
      <rect
        key={i}
        x={-8}
        y={-92 - i * 6}
        width={16}
        height={56}
        rx={8}
        fill={RED}
        transform={`rotate(${a})`}
      />
    ))}
  </g>
);

const Half: React.FC<{ quiet: boolean; frame: number; heading: string; caption: string }> = ({
  quiet, frame, heading, caption,
}) => {
  const color = quiet ? BRAND.orange : RED;

  let x: number;
  let y: number;
  let rot: number;
  const strike = quiet ? 46 : 16;

  if (quiet) {
    // travels in slowly, touches once, stops dead
    const e = 1 - Math.pow(
      1 - interpolate(frame, [0, strike], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      }),
      2.4,
    );
    x = interpolate(e, [0, 1], [TOE_X + 210, TOE_X]);
    y = interpolate(e, [0, 1], [LEDGE_Y - 360, LEDGE_Y]);
    rot = interpolate(e, [0, 1], [-10, 0]);
  } else {
    // strikes hard, rebounds, skids off the tip, then two nervous corrections
    const keys = [0, strike, 24, 34, 44, 56, 66, 78, 88, 120];
    x = interpolate(frame, keys,
      [TOE_X + 230, TOE_X + 4, TOE_X + 30, TOE_X + 130, TOE_X + 146,
       TOE_X + 40, TOE_X + 66, TOE_X + 10, TOE_X, TOE_X],
      { extrapolateRight: "clamp" });
    y = interpolate(frame, keys,
      [LEDGE_Y - 380, LEDGE_Y, LEDGE_Y - 64, LEDGE_Y + 44, LEDGE_Y + 52,
       LEDGE_Y, LEDGE_Y - 36, LEDGE_Y, LEDGE_Y, LEDGE_Y],
      { extrapolateRight: "clamp" });
    rot = interpolate(frame, keys, [-16, -3, -11, 10, 13, -4, -8, 0, 0, 0],
      { extrapolateRight: "clamp" });
  }

  const flash = interpolate(frame, [strike, strike + 3, strike + 18], [0, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const ring = interpolate(frame, [strike, strike + 28], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  // the verdict only appears once the foot has actually stopped moving
  const settleAt = quiet ? strike + 8 : 90;
  const settle = interpolate(frame, [settleAt, settleAt + 12], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const patch = quiet ? 200 : 50;

  return (
    <svg width={1080} height={HALF_H} viewBox={`0 0 1080 ${HALF_H}`}>
      <Wall />

      {quiet && ring > 0 && ring < 1 && (
        <circle
          cx={TOE_X + 70}
          cy={LEDGE_Y}
          r={34 + ring * 190}
          fill="none"
          stroke={BRAND.orange}
          strokeWidth={12}
          opacity={(1 - ring) * 0.85}
        />
      )}
      {!quiet && <Spark o={flash} />}

      <Shoe x={x} y={y} rot={rot} />

      <g opacity={settle}>
        <rect x={TOE_X} y={LEDGE_Y - 11} width={patch} height={22} rx={11} fill={color} />
        {quiet ? (
          <Arrow x={TOE_X + 120} y={LEDGE_Y + 26} dx={-120} dy={230} color={color} />
        ) : (
          <Arrow x={TOE_X + 54} y={LEDGE_Y + 26} dx={210} dy={180} color={color} />
        )}
      </g>

      <text x={56} y={132} style={{ ...label, fontSize: 108, fill: color }}>
        {heading}
      </text>
      <text x={540} y={HALF_H - 70} textAnchor="middle" style={{ ...label, fontSize: 58 }}>
        {caption}
      </text>
    </svg>
  );
};

export const CONTACT_SECONDS = 4;

export const Contact: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: BRAND.ink }}>
      <Half quiet={false} frame={frame} heading="STOMP" caption="bounces off the hold" />
      <div style={{ height: 2, backgroundColor: "#2E2E36" }} />
      <Half quiet frame={frame} heading="QUIET" caption="presses into the hold" />
    </AbsoluteFill>
  );
};
