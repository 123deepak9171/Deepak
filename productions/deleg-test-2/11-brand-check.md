# 11-brand-check: DMW CRUSHER X1 (deleg-test-2)
- Reviewed against: brand/BRAND_RULES.md, 00-brief.md. No render exists; none was made.
- Reviewed files: 01-script.md, script.txt, 02-hooks.md, images/thumbnail.png (viewed with Read, 1920x1080).
- Facts given by owner: NONE (price not confirmed, no specs, no launch date).

## Overall verdict
| Item | Verdict | Owner |
|---|---|---|
| 01-script.md + script.txt | APPROVED WITH NOTES | script-writer |
| 02-hooks.md | APPROVED WITH NOTES | viral-hook |
| images/thumbnail.png | FIXES NEEDED (before public use) | image-generation |

Nothing here is ready to publish until the owner answers the [CONFIRM] items in section 4.

## 1. Script (01-script.md, script.txt): APPROVED WITH NOTES
PASS
- Name "DESI MINING WALA" / "DMW CRUSHER X1" spelled correctly (line 2, 6 on-screen; script.txt line 2).
- Tagline "Asli Desi Mining Knowledge" and CTA "Subscribe karo, Bell dabao!" exact, in row 6 / script.txt line 6.
- No price number, no spec numbers, no No.1, no testimonial, no abuse/political/caste. Tone respectful Hinglish, "Ram Ram bhai" fine.
- Safety row 5 (Helmet + PPE) present.
- Colours/fonts: gold #F5A623, saffron #FF6B1A, dark #111111 correct; Mukta ExtraBold captions; safe areas noted.
- Logo "centre, not covered by text" (row 6) OK.

NOTES / FIXES (owner: script-writer)
1. Row 1 + script.txt line 1 "Naya crusher aa gaya!" and row 2 "ekdum naya!" / badge "NEW": states the product is launched. Owner has not confirmed launch status. Keep only if owner confirms; otherwise use neutral wording (e.g. "Ek naya crusher aa raha hai" is still a launch claim, so also needs OK).
2. Row 6 / script.txt line 6 "Price jaldi announce hoga": this is a promise about future announcement that the owner has not given. Soft fake-urgency/unconfirmed offer risk. Mark [CONFIRM] in VO or replace with "Price ke liye comment karo" ([CONFIRM] contact method). Same for row 4 "specs jaldi bataenge" (promise about future, needs OK).
3. Row 3 "mazboot build" is a quality claim not given by the owner. The script already marks it [CONFIRM]; keep it marked, and prefer removing it from script.txt (captions file) until confirmed, because script.txt has no [CONFIRM] marker and would be captioned as fact.
4. On-screen "[CONFIRM]" tags (rows 3, 4, 6) must not reach the final render. Remove before render.
5. Row 6 is dense (3 CTA elements in 5 s) and tagline sits in the last ~1.5 s. Acceptable, but make sure the bottom-20% safe area is kept for the CTA text.
6. Logo path: script uses assets/demo/dmw_logo.png. The brand-rule path assets/logos/logo.png does not exist in the repo (assets/logos/ is empty). Demo logo is acceptable for this test; owner should confirm it is the official logo.
7. Visual note row 2/3: product photo is the demo placeholder, see section 4.

## 2. Hooks (02-hooks.md): APPROVED WITH NOTES
PASS
- Name spelled correctly; no price/specs/No.1; tone respectful; word limits followed; safe-area noted; PPE mentioned in hook 4.
- Thumbnail colour guidance matches brand tokens. Subtext "DESI MINING WALA" correct.

NOTES / FIXES (owner: viral-hook)
1. Hooks 1, 3 (partly), 5 and thumbnail options 1 and 3 use launch words: "NAYA", "kuch naya aa raha hai", "NAYA CRUSHER AA GAYA?", "X1 AA RAHA HAI?". Hook 1 (the RECOMMENDED) also says "aa raha hai" which is a launch/coming-soon claim. Brief says "new launch" so these are likely fine, but launch status/timing is unconfirmed: all need owner confirmation. Hook 5 already carries [CONFIRM]; add the same [CONFIRM] flag to Hook 1 and thumbnail option 1.
2. Hook 1 visual says product photo is revealed: the only photo is a placeholder (section 4). Add a note that the real X1 photo is needed.
3. Hook 2 "Crusher lene se pehle ye 20 second zaroor dekh lena" is advice, not fake urgency: OK. Hook 2 visual "contractor POV on site" needs owner/permission footage and PPE visible; note it.
4. Hook 4 "Khadaan wale bhaiyo" is respectful and fine. "Bhaiyo" is male-addressed; acceptable.
5. Notes section suggests "Price ke liye comment ya DM karo": fine, contact method is [CONFIRM] as stated.

## 3. Thumbnail (images/thumbnail.png): FIXES NEEDED
Viewed the PNG directly.

PASS
- Size 1920x1080 (16:9), valid for YouTube.
- Text "NAYA CRUSHER X1" white Poppins-style bold on dark #111111: readable, correct spelling. "DESI MINING WALA" in gold, correct, all caps.
- "NEW" badge is saffron with white text: matches brand token.
- No price, no specs, no No.1, no fake urgency.
- Logo top-right, 173x173 from a 600x600 square source: not stretched, not recoloured (gold ring and DMW kept), not covered by text. The dark disc behind it is a backing only: acceptable, logo itself unchanged.
- Text is clear of the logo.

FIXES (owner: image-generation)
1. BLOCKER: right ~55% of the frame is the placeholder fractal image (neon pink/purple/green) with a "PRODUCT" caption. It is not a crusher and is misleading, and pink/purple/neon is against the brand rule "avoid neon/purple looks" and off the earthy-mining grade. Do not publish. Re-make with the real X1 photo (owner to supply) and the earthy-mining grade. If no photo is available, use a dark #111111 / charcoal background or the mine background with an explicit "photo coming" decision from the owner, rather than the fractal.
2. The "PRODUCT" placeholder text at bottom-right (about x 1100-1620, y 900-980) overlaps the fractal and is cut by the fractal edge; it will be removed with fix 1. Keep the bottom-right timestamp zone clear on the new version.
3. "NAYA" + "NEW" badge duplicate each other and both assert launch status: confirm with owner (section 4). If launch not confirmed, replace badge/text.
4. Minor: "DESI MINING WALA" gold subline is smaller than the headline: fine. Headline text has a slight dark shadow, ok. No change needed.

## 4. Open questions for the owner (all [CONFIRM])
1. Is DMW CRUSHER X1 actually launched? If not, remove "NAYA / NEW / aa gaya / aa raha hai" (or get OK).
2. Price: not confirmed. Keep out. Is "Price jaldi announce hoga" or "comment/DM for price" acceptable?
3. Specs (TPH, jaw size, motor, weight): none given, none used. "Mazboot build" needs OK.
4. Launch date, availability, offers: none given, none used.
5. Real X1 product photo: assets/demo/product_photo.jpg is a demo placeholder (fractal image with "PRODUCT" text), NOT a crusher. It must not appear in any public output (reel reveal or thumbnail).
6. Is assets/demo/dmw_logo.png the official logo? (assets/logos/logo.png is missing.)
7. PPE footage/icon: need user-owned footage or an icon.

## 5. Fix list by owner
- script-writer: items 1-4 in section 1 (launch wording, price/specs future promises, mazboot build in script.txt, remove [CONFIRM] tags before render).
- viral-hook: items 1-3 in section 2 (add [CONFIRM] to Hook 1 and thumbnail option 1; placeholder photo note).
- image-generation: thumbnail fixes 1-3 in section 3 (replace fractal placeholder, remove "PRODUCT" text, off-brand neon colours).
