import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { BaseProps, BRAND, FONT_STACK } from "../brand";
import { Background } from "./Background";

export type TitleCardProps = BaseProps & { title: string; subtitle: string };

/** Section title / chapter card with underline grow. */
export const TitleCard: React.FC<TitleCardProps> = ({ title, subtitle, accent = BRAND.gold }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const unit = Math.min(width, height);
  const inn = spring({ frame, fps, config: { damping: 200 } });
  const fadeOut = interpolate(frame, [durationInFrames - 0.3 * fps, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <Background accent={accent} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", padding: unit * 0.06, textAlign: "center" }}>
        <div style={{ fontFamily: FONT_STACK, fontWeight: 800, fontSize: unit * 0.11, color: BRAND.white, opacity: inn, scale: String(interpolate(inn, [0, 1], [0.8, 1])) }}>
          {title}
        </div>
        <div style={{ height: unit * 0.012, width: `${interpolate(inn, [0, 1], [0, 40])}%`, background: accent, marginTop: unit * 0.02, borderRadius: unit }} />
        {subtitle ? <div style={{ fontFamily: FONT_STACK, fontSize: unit * 0.05, color: accent, marginTop: unit * 0.03, opacity: inn }}>{subtitle}</div> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
