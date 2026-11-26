import { AbsoluteFill, Easing, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { asset, BaseProps, BRAND, FONT_STACK } from "../brand";
import { Background } from "./Background";

export type LogoRevealProps = BaseProps & { logo: string | null; tagline: string };

/** Logo animation: scale-pop + light ring + brand name typing + tagline fade. */
export const LogoReveal: React.FC<LogoRevealProps> = ({ logo, tagline, accent = BRAND.gold }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const unit = Math.min(width, height);
  const pop = spring({ frame, fps, config: { damping: 12, stiffness: 120 } });
  const name = BRAND.name;
  const chars = Math.round(interpolate(frame, [0.5 * fps, 1.5 * fps], [0, name.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const fadeOut = interpolate(frame, [durationInFrames - 0.4 * fps, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const src = asset(logo);
  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <Background accent={accent} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: unit * 0.04 }}>
        <div
          style={{
            width: unit * 0.38,
            height: unit * 0.38,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: `0 0 ${unit * 0.08}px ${accent}`,
            border: `${unit * 0.008}px solid ${accent}`,
            background: BRAND.charcoal,
            scale: String(pop),
            rotate: `${interpolate(pop, [0, 1], [-25, 0])}deg`,
          }}
        >
          {src ? (
            <Img src={src} style={{ width: "78%", height: "78%", objectFit: "contain" }} />
          ) : (
            <div style={{ fontFamily: FONT_STACK, fontSize: unit * 0.13, color: accent, fontWeight: 800 }}>DMW</div>
          )}
        </div>
        <div style={{ fontFamily: FONT_STACK, fontWeight: 800, fontSize: unit * 0.085, color: BRAND.white, letterSpacing: unit * 0.004 }}>
          {name.slice(0, chars)}
        </div>
        <div
          style={{
            fontFamily: FONT_STACK,
            fontSize: unit * 0.045,
            color: accent,
            opacity: interpolate(frame, [1.4 * fps, 2 * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
            translate: `0px ${interpolate(frame, [1.4 * fps, 2 * fps], [unit * 0.03, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) })}px`,
          }}
        >
          {tagline}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
