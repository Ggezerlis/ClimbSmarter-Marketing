import "./index.css";
import { Composition } from "remotion";
import { HelloWorld, myCompSchema } from "./HelloWorld";
import { Logo, myCompSchema2 } from "./HelloWorld/Logo";
import { Reel, REEL_DURATION } from "./Reel";
import { Ad, Ad15, AD_DURATION, AD15_DURATION } from "./Ad";
import { Spot, S } from "./Spot";
import { SPOTS } from "./spots";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* The five spots. Each is data in src/spots + a master mix in public. */}
      {SPOTS.map((spot) => (
        <Composition
          key={spot.slug}
          id={spot.slug.charAt(0).toUpperCase() + spot.slug.slice(1)}
          component={Spot}
          defaultProps={{ spot }}
          durationInFrames={S(spot.seconds)}
          fps={30}
          width={1080}
          height={1920}
        />
      ))}

      <Composition
        // 15s paid cut — same grid, tighter; sized for feed/story placements
        id="Ad15"
        component={Ad15}
        durationInFrames={AD15_DURATION}
        fps={30}
        width={1080}
        height={1920}
      />

      <Composition
        // The ad: beat-locked cut, original score, burned-in captions
        id="Ad"
        component={Ad}
        durationInFrames={AD_DURATION}
        fps={30}
        width={1080}
        height={1920}
      />

      <Composition
        // Vertical before/after marketing reel (V1 fail -> V10 send)
        id="Reel"
        component={Reel}
        durationInFrames={REEL_DURATION}
        fps={30}
        width={1080}
        height={1920}
      />

      <Composition
        // You can take the "id" to render a video:
        // npx remotion render HelloWorld
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        // You can override these props for each render:
        // https://www.remotion.dev/docs/parametrized-rendering
        schema={myCompSchema}
        defaultProps={{
          titleText: "Welcome to Remotion",
          titleColor: "#000000",
          logoColor1: "#91EAE4",
          logoColor2: "#86A8E7",
        }}
      />

      {/* Mount any React component to make it show up in the sidebar and work on it individually! */}
      <Composition
        id="OnlyLogo"
        component={Logo}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        schema={myCompSchema2}
        defaultProps={{
          logoColor1: "#91dAE2" as const,
          logoColor2: "#86A8E7" as const,
        }}
      />
    </>
  );
};
