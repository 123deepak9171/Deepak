import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { asset, BaseProps, BRAND, FONT_STACK } from "../brand";
import { Background } from "./Background";

export type OutroProps = BaseProps & { logo: string | null; cta: string };

/** End screen with logo + call-to-action pulse. */
export const Outro: React.FC<OutroProps> = ({ logo, cta, accent = BRAND.gold }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const unit = Math.min(width, height);
  const inn = spring({ frame, fps, config: { damping: 15 } });
  const pulse = 1 + 0.04 * Math.sin((frame / fps) * Math.PI * 2);
  const src = asset(logo);
  return (
    <AbsoluteFill>
      <Background accent={accent} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: unit * 0.05, textAlign: "center", padding: unit * 0.05 }}>
        {src ? <Img src={src} style={{ width: unit * 0.28, height: unit * 0.28, objectFit: "contain", scale: String(inn) }} /> : null}
        <div style={{ fontFamily: FONT_STACK, fontWeight: 800, fontSize: unit * 0.08, color: BRAND.white, opacity: inn }}>{BRAND.name}</div>
        <div
          style={{
            fontFamily: FONT_STACK,
            fontWeight: 800,
            fontSize: unit * 0.05,
            color: BRAND.dark,
            background: accent,
            padding: `${unit * 0.015}px ${unit * 0.04}px`,
            borderRadius: unit,
            scale: String(inn * pulse),
          }}
        >
          {cta}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
