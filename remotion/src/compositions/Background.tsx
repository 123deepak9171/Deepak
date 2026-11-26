import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BRAND } from "../brand";

/** Animated dark background with moving gold light sweep (no CSS animations). */
export const Background: React.FC<{ accent?: string }> = ({ accent = BRAND.gold }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: BRAND.dark, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 45%, ${BRAND.charcoal} 0%, ${BRAND.dark} 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.35,
          background: `linear-gradient(110deg, transparent 35%, ${accent} 50%, transparent 65%)`,
          translate: `${interpolate(frame, [0, durationInFrames], [-120, 120])}% 0%`,
        }}
      />
    </AbsoluteFill>
  );
};
