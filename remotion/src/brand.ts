import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// DESI MINING WALA brand system (change colors here)
export const BRAND = {
  name: "DESI MINING WALA",
  gold: "#F5A623",
  saffron: "#FF6B1A",
  dark: "#111111",
  charcoal: "#1E1E1E",
  white: "#FFFFFF",
};

export const HEADING_FONT = "DMW Heading";
export const HINDI_FONT = "DMW Hindi";

loadFont({ family: HEADING_FONT, url: staticFile("fonts/Poppins-ExtraBold.ttf"), weight: "800" });
loadFont({ family: HINDI_FONT, url: staticFile("fonts/Mukta-ExtraBold.ttf"), weight: "800" });

export const FONT_STACK = `"${HEADING_FONT}", "${HINDI_FONT}", sans-serif`;

/** Common props shared by all DMW compositions. Size/duration come from the pipeline. */
export type BaseProps = {
  width: number;
  height: number;
  durationSec: number;
  fps: number;
  accent?: string;
};

/** Image paths are relative to remotion/public (the pipeline copies files there). */
export const asset = (p?: string | null) => (p ? staticFile(p) : null);
