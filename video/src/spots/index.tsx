import React from "react";
import { Spot, SpotDef, Caption, Shot } from "../Spot";

import adaptData from "./adapt.json";
import askData from "./ask.json";
import fuelData from "./fuel.json";
import grindData from "./grind.json";
import quietfeetData from "./quietfeet.json";

/**
 * The picture edit and the caption timings come out of tools/build_spots.py -
 * they have to match the master mix frame for frame, so they are generated
 * rather than typed. What lives here is the layer that only exists on screen:
 * the statement text, the highlight boxes, and the end card.
 */
type Built = { shots: Shot[]; captions: Caption[] };

const spot = (
  slug: string,
  data: Built,
  rest: Omit<SpotDef, "slug" | "master" | "shots" | "captions">,
): SpotDef => ({
  slug,
  master: `${slug}/master.mp3`,
  shots: data.shots,
  captions: data.captions,
  ...rest,
});

// ---------------------------------------------------------------------------

export const ADAPT = spot("adapt", adaptData as Built, {
  seconds: 20,
  // the first two seconds are the statement, and the end card speaks for itself
  quiet: [[0, 2.0], [17.5, 20]],
  beats: [
    {
      at: 0.15,
      dur: 1.85,
      kicker: "MOST TRAINING PLANS",
      text: "don't know\nyou had a\n*bad week.*",
      y: "mid",
      size: 112,
    },
  ],
  // The answer he taps. Coordinates are measured off the cut clip rather than
  // guessed, and this is the one screen in the five that holds still long
  // enough to point at - everything else scrolls under the box.
  focus: [{ at: 3.35, dur: 0.65, x: 63.7, y: 28.3, w: 27.3, h: 12.6 }],
  flashes: [{ at: 2.0, amp: 0.4 }, { at: 15.0, amp: 0.34 }],
  end: {
    at: 17.5,
    kicker: "IT DOESN'T JUST TRACK",
    line1: "It asks. Then it",
    line2: "rewrites the plan.",
    sub: "14 days free · no card",
  },
});

export const ASK = spot("ask", askData as Built, {
  seconds: 20,
  quiet: [[0, 2.0], [17.5, 20]],
  beats: [
    {
      at: 0.15,
      dur: 1.85,
      kicker: "TWO YEARS OF GUESSING",
      text: "So I just\n*asked it.*",
      y: "mid",
      size: 120,
    },
  ],
  flashes: [{ at: 2.0, amp: 0.38 }, { at: 11.0, amp: 0.34 }],
  end: {
    at: 17.5,
    kicker: "A COACH IN THE APP",
    line1: "Ask it anything.",
    line2: "Any time.",
    sub: "14 days free · no card",
  },
});

export const FUEL = spot("fuel", fuelData as Built, {
  seconds: 18,
  quiet: [[0, 2.0], [15.5, 18]],
  beats: [
    {
      at: 0.15,
      dur: 1.85,
      kicker: "NOBODY TALKS ABOUT",
      text: "the other\n*half* of\ntraining.",
      y: "mid",
      size: 112,
    },
  ],
  flashes: [{ at: 2.0, amp: 0.38 }, { at: 13.5, amp: 0.34 }],
  end: {
    at: 15.5,
    kicker: "TRAINING + NUTRITION",
    line1: "One plan.",
    line2: "Both halves.",
    sub: "14 days free · no card",
  },
});

export const GRIND = spot("grind", grindData as Built, {
  seconds: 22,
  quiet: [[0, 2.0], [19.5, 22]],
  beats: [
    {
      at: 0.15,
      dur: 1.85,
      kicker: "TODAY'S SESSION",
      text: "*Fail.*\nOn purpose.",
      y: "mid",
      size: 128,
    },
  ],
  flashes: [{ at: 2.0, amp: 0.36 }, { at: 12.0, amp: 0.55 }],
  end: {
    at: 19.5,
    kicker: "BUILT AROUND YOUR PROJECT",
    line1: "Stop guessing.",
    line2: "Start sending.",
    sub: "14 days free · no card",
  },
});

export const QUIETFEET = spot("quietfeet", quietfeetData as Built, {
  seconds: 20,
  quiet: [[0, 2.0], [18.0, 20]],
  beats: [
    {
      at: 0.15,
      dur: 1.85,
      kicker: "TIP 01",
      text: "Loud feet =\n*wasted energy.*",
      y: "mid",
      size: 104,
    },
  ],
  flashes: [{ at: 2.0, amp: 0.34 }],
  end: {
    at: 18.0,
    soft: true,
    kicker: "QUIET FEET · TIP 01",
    line1: "Want more",
    line2: "coaching like this?",
    sub: "Your plan is built out of them",
  },
});

export const SPOTS = [ADAPT, ASK, FUEL, GRIND, QUIETFEET];

export const AdaptSpot: React.FC = () => <Spot spot={ADAPT} />;
export const AskSpot: React.FC = () => <Spot spot={ASK} />;
export const FuelSpot: React.FC = () => <Spot spot={FUEL} />;
export const GrindSpot: React.FC = () => <Spot spot={GRIND} />;
export const QuietFeetSpot: React.FC = () => <Spot spot={QUIETFEET} />;
