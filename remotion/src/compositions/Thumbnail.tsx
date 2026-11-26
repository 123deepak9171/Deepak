import { AbsoluteFill, Img } from "remotion";
import { asset, BaseProps, BRAND, FONT_STACK } from "../brand";

export type ThumbnailProps = BaseProps & {
  headline: string;
  subline: string;
  image: string | null;
  logo: string | null;
  badge: string;
};

/** Static YouTube thumbnail / poster (render with `remotion still`). Designed, not AI-generated. */
export const Thumbnail: React.FC<ThumbnailProps> = ({ width, height, headline, subline, image, logo, badge, accent = BRAND.gold }) => {
  const unit = Math.min(width, height);
  const vertical = height > width;
  const img = asset(image);
  const lg = asset(logo);
  return (
    <AbsoluteFill style={{ background: BRAND.dark, overflow: "hidden" }}>
      {img ? (
        <Img
          src={img}
          style={{
            position: "absolute",
            right: 0,
            top: 0,
            width: vertical ? "100%" : "58%",
            height: vertical ? "55%" : "100%",
            objectFit: "cover",
          }}
        />
      ) : null}
      <AbsoluteFill
        style={{
          background: vertical
            ? `linear-gradient(180deg, transparent 30%, ${BRAND.dark} 58%)`
            : `linear-gradient(90deg, ${BRAND.dark} 40%, transparent 75%)`,
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: vertical ? "flex-end" : "center",
          padding: unit * 0.07,
          gap: unit * 0.03,
        }}
      >
        {badge ? (
          <div
            style={{
              alignSelf: "flex-start",
              background: BRAND.saffron,
              color: BRAND.white,
              fontFamily: FONT_STACK,
              fontWeight: 800,
              fontSize: unit * 0.06,
              padding: `${unit * 0.01}px ${unit * 0.03}px`,
              borderRadius: unit * 0.015,
              rotate: "-3deg",
            }}
          >
            {badge}
          </div>
        ) : null}
        <div
          style={{
            fontFamily: FONT_STACK,
            fontWeight: 800,
            fontSize: unit * (vertical ? 0.13 : 0.15),
            lineHeight: 1.0,
            color: BRAND.white,
            maxWidth: vertical ? "100%" : "55%",
            textShadow: `0 ${unit * 0.01}px 0 ${BRAND.dark}`,
            WebkitTextStroke: `${unit * 0.004}px ${BRAND.dark}`,
          }}
        >
          {headline}
        </div>
        {subline ? (
          <div style={{ fontFamily: FONT_STACK, fontWeight: 800, fontSize: unit * 0.065, color: accent, maxWidth: vertical ? "100%" : "55%" }}>
            {subline}
          </div>
        ) : null}
      </AbsoluteFill>
      {lg ? (
        <Img src={lg} style={{ position: "absolute", right: unit * 0.04, top: unit * 0.04, width: unit * 0.16, height: unit * 0.16, objectFit: "contain" }} />
      ) : null}
    </AbsoluteFill>
  );
};
