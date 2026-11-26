import { CalculateMetadataFunction, Composition } from "remotion";
import { BaseProps } from "./brand";
import { LogoReveal, LogoRevealProps } from "./compositions/LogoReveal";
import { ProductReveal, ProductRevealProps } from "./compositions/ProductReveal";
import { TitleCard, TitleCardProps } from "./compositions/TitleCard";
import { Outro, OutroProps } from "./compositions/Outro";

// Every composition reads its size + length from input props, so the Python
// pipeline can render 16:9, 9:16 or 1:1 with any duration.
function meta<T extends BaseProps>(): CalculateMetadataFunction<T> {
  return ({ props }) => ({
    width: props.width,
    height: props.height,
    fps: props.fps,
    durationInFrames: Math.max(1, Math.round(props.durationSec * props.fps)),
  });
}

const base = { width: 1920, height: 1080, fps: 30 };

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="LogoReveal"
      component={LogoReveal}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={90}
      defaultProps={{ ...base, durationSec: 3, logo: null, tagline: "Asli Desi Mining Knowledge" } satisfies LogoRevealProps}
      calculateMetadata={meta<LogoRevealProps>()}
    />
    <Composition
      id="ProductReveal"
      component={ProductReveal}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={120}
      defaultProps={{ ...base, durationSec: 4, title: "NEW PRODUCT", subtitle: "Ab aur bhi powerful", image: null, price: "" } satisfies ProductRevealProps}
      calculateMetadata={meta<ProductRevealProps>()}
    />
    <Composition
      id="TitleCard"
      component={TitleCard}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={75}
      defaultProps={{ ...base, durationSec: 2.5, title: "Aaj Ka Topic", subtitle: "" } satisfies TitleCardProps}
      calculateMetadata={meta<TitleCardProps>()}
    />
    <Composition
      id="Outro"
      component={Outro}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={90}
      defaultProps={{ ...base, durationSec: 3, logo: null, cta: "Subscribe karo, Bell dabao!" } satisfies OutroProps}
      calculateMetadata={meta<OutroProps>()}
    />
  </>
);
