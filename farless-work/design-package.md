# Farless: Design Package (Tier 1, single journey)

## 1. The brand premise

One word: **less**. Farless puts boiling, filtered, sparkling, hot, and cold water into one quiet tap, so the kettle, the filter jug, the soda machine, and the bottles leave the counter. The whole site teaches and sells that one idea: a calmer kitchen with far less in it. The hero pours one perfect glass of sparkling water, lemon and lime from the tap itself, no bottle in sight. The interactive moment enacts the push-and-turn safety dial. The closing line asks the visitor to make room.

## 2. The palette as CSS tokens

Direction from the footage's world: warm white lime plaster, pale limestone, polished chrome, crisp morning light, with lemon and lime as the only color. One deep mineral blue for the buy button. Light and airy, in the spirit of Vipp and Gessi. Exact values get resampled from the approved footage after the video gate.

```css
:root{
  --canvas:#E9E7E3;        /* limestone mist, never pure white */
  --panel:#F3F2EF;         /* raised stone */
  --accent:#24505C;        /* deep mineral blue: the buy button and rare emphasis */
  --accent-hover:#1B3F49;
  --accent-muted:#9FB7BC;  /* borders, glows, bubbles */
  --text-secondary:#5A6166;
  --text-primary:#1F2427;
}
```

Hero text over the footage: the film is bright (warm white plaster), so hero bands run dark text over soft light mist scrims rather than light text over dark scrims. Decided against the real frames after the video gate, then audited at 3.5:1 worst pixel.

## 3. The type trio

- Display: **Familjen Grotesk** 400 and 500. Scandinavian grotesk with quiet character, from the Vipp world.
- Body: **Hanken Grotesk** 400 and 500.
- Mono (small labels, temperatures): **IBM Plex Mono** 400.

## 4. The band map

Concept (revised after owner feedback): a centered, locked-off shot. Sparkling water pours from the Farless spout straight down the center line into a tall glass of ice, lemon and lime, filling it from empty to full as the visitor scrolls. Hero height about 400vh. Ranges are starting points, validated by the flick test.

| Band | Range (starting point) | Footage moment | Copy (verbatim) | Entrance |
|---|---|---|---|---|
| 1 | 0.00 to 0.30 | The first ribbon of sparkling water leaves the nozzle; the glass holds only ice and citrus | Left column: "Farless." / Right column: "Five waters. One tap." | Blur-to-sharp, echoing the first clear drop (load ramp on band one) |
| 2 | 0.34 to 0.64 | The stream runs full, the glass fills, ice lifts, citrus wheels rise | Left: "Boiling. Filtered." / Right: "Sparkling. Hot. Cold." | Drift-down, word by word, echoing the pour |
| 3 (settle) | 0.70 to 1.00 | At rest: the glass full and fizzing, the stream falling softly into it | Upper left: "Far less on your counter." / Upper right: "No kettle. No bottles. No soda machine. Just one tap." / button "Buy Farless" | Word-by-word rise into a staged settle |

Layout: the pour owns the center lane and is never covered. Text lives in the open plaster wall on both sides, using the two-sided scrim variant (one scrim per column, center lane untouched). The faucet column sits left of center, so the left text column stays in the outer left third.

## 5. The static-hero copy block

Over the ending frame, for phones and reduced motion:

- Headline: "Far less on your counter."
- Subline: "Boiling, filtered, sparkling, hot and cold water. All from one quiet tap."
- Button: "Buy Farless"

## 6. The below-fold outline

Nav: Farless wordmark (inline SVG), links "Five waters", "Safety", "Design", "Questions", button "Buy".

1. **Five waters** (five equal cards, each with a small mono temperature label)
   - Boiling, "100°C": "Tea in the time it takes to reach for a cup."
   - Sparkling: "Fresh bubbles every glass. No more flat bottles."
   - Filtered: "Clean drinking water, straight from the tap."
   - Hot: "For washing up and everyday cooking."
   - Cold: "Just water, the way it should be."
2. **What leaves your counter** (a quiet before and after row)
   - Kicker: "One tap replaces"
   - Items: "The kettle." "The filter jug." "The soda machine." "The bottles."
   - Line: "Fewer things. A calmer kitchen."
3. **Safety, the interactive moment: press and turn**
   - Headline: "Boiling only when you mean it."
   - Body: "Boiling water flows only when you push the dial and turn it at the same time. Small hands can't do it by accident."
   - Interaction: a drawn steel dial. The visitor presses and holds; the dial turns and a boiling stream line fills. Releasing early eases it back. Completing it reveals "Push. Turn. Boiling." Reduced motion shows the completed state.
4. **Design** (ending frame reused as the image)
   - Headline: "Made to be looked at."
   - Body: "Brushed steel and one clean arc. Nothing to hide, and nothing to add."
5. **Questions** (real objections from research, answered only with confirmed facts)
   - "Is it safe with children around?" / "Yes. Boiling water needs a push and a turn at the same time, so it can't start by accident."
   - "What if something goes wrong?" / "Every Farless comes with a 5-year warranty."
   - "Does it really replace the kettle?" / "Yes. Boiling water is ready the moment you turn the dial. No waiting, no refilling."
   - "Will it still make sparkling water when I'm out of bottles?" / "There are no bottles to run out of. Sparkling water comes straight from the tap."
   - Pending facts from the owner before more answers: filter change schedule and cost, installation, hard water.
6. **Final call to action**
   - Headline: "Make room."
   - Line: "Five waters. One tap. Far less on your counter."
   - Button: "Buy Farless" (links to the online shop; URL pending from the owner)
   - No form: the button goes straight to the existing checkout.
7. **Footer**: "© Farless", nav links repeated, plus an imagery note if the owner chooses one ("Kitchen scenes are digitally rendered from the real product.").

No testimonials: there are no real reviews yet, and invented ones are off the table.

## 7. The vector layer plan

- **Signature element, the arc:** a hairline SVG arc traced from the spout's curve that draws itself on scroll at each section seam, so the page reads as one continuous line of steel. Removing it would cost the page its thread.
- Whisper-level bubbles rising slowly behind the Sparkling card and the final call to action.
- A fixed background environment layer: a soft caustic light drift, as if from water, cycling over 70 seconds.
- All of it honors reduced motion: lines shown drawn, drift and bubbles stopped.

## 8. The engineering list

Blob fetch with the loading ring (plain Blob if under 8 MB), the dt-normalized lerp, gated seeks with the error escape, delta-gated DOM writes, band pacing with the flick test, the four-layer legibility system with the worst-frame audit, the five static-hero gates kept live with change listeners, complete without the video, the quality floor, and the whole-site-animated standard. All per `scrub-pipeline.md` and Phase 8 of the skill.

## 9. The copy gate line

Every viewer-facing line above ships verbatim. The built page must pass the Phase 9 grep gate (zero em dashes, zero stock words) and the body-copy sweep for AI tells before anyone sees it. Deliberate brand devices here ("Five waters. One tap.", "Push. Turn. Boiling.", the "The kettle. The filter jug." staccato) are craft and stay.
