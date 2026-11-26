import { AbsoluteFill, Easing, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { asset, BaseProps, BRAND, FONT_STACK } from "../brand";
import { Background } from "./Background";

export type ProductRevealProps = BaseProps & { title: string; subtitle: string; image: string | null; price: string };

/** Product reveal: curtain wipe, product image rises with glow, title slides in. */
export const ProductReveal: React.FC<ProductRevealProps> = ({ title, subtitle, image, price, accent = BRAND.saffron }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const unit = Math.min(width, height);
  const vertical = height > width;
  const wipe = interpolate(frame, [0, 0.6 * fps], [0, 100], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const rise = spring({ frame: frame - 0.4 * fps, fps, config: { damping: 14 } });
  const titleIn = spring({ frame: frame - 0.9 * fps, fps, config: { damping: 200 } });
  const fadeOut = interpolate(frame, [durationInFrames - 0.4 * fps, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const src = asset(image);
  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <Background accent={accent} />
      <AbsoluteFill style={{ background: accent, clipPath: `inset(0 ${wipe}% 0 0)` }} />
      <AbsoluteFill
        style={{
          flexDirection: vertical ? "column" : "row",
          alignItems: "center",
          justifyContent: "center",
          gap: unit * 0.06,
          padding: unit * 0.06,
        }}
      >
        <div
          style={{
            width: unit * 0.5,
            height: unit * 0.5,
            borderRadius: unit * 0.04,
            background: BRAND.charcoal,
            boxShadow: `0 0 ${unit * 0.1}px ${accent}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
            translate: `0px ${interpolate(rise, [0, 1], [unit * 0.4, 0])}px`,
            opacity: rise,
          }}
        >
          {src ? (
            <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div style={{ fontFamily: FONT_STACK, fontSize: unit * 0.2, color: accent }}>★</div>
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: vertical ? "center" : "flex-start", textAlign: vertical ? "center" : "left", maxWidth: vertical ? "90%" : "45%" }}>
          <div
            style={{
              fontFamily: FONT_STACK,
              fontWeight: 800,
              fontSize: unit * 0.1,
              lineHeight: 1.05,
              color: BRAND.white,
              opacity: titleIn,
              translate: `${interpolate(titleIn, [0, 1], [unit * 0.15, 0])}px 0px`,
            }}
          >
            {title}
          </div>
          <div style={{ fontFamily: FONT_STACK, fontSize: unit * 0.05, color: accent, marginTop: unit * 0.02, opacity: titleIn }}>{subtitle}</div>
          {price ? (
            <div
              style={{
                marginTop: unit * 0.03,
                fontFamily: FONT_STACK,
                fontWeight: 800,
                fontSize: unit * 0.06,
                color: BRAND.dark,
                background: BRAND.gold,
                padding: `${unit * 0.01}px ${unit * 0.03}px`,
                borderRadius: unit * 0.015,
                scale: String(spring({ frame: frame - 1.5 * fps, fps, config: { damping: 10 } })),
              }}
            >
              {price}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
