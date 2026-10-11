# Farless: Design Package (Tier 1, single journey)

## 1. The brand premise

One word: **less**. Farless puts boiling, filtered, sparkling, hot, and cold water into one quiet tap, so the kettle, the filter jug, the soda machine, and the bottles leave the counter. The whole site teaches and sells that one idea: a calmer kitchen with far less in it. The hero pours one perfect glass of sparkling water, lemon and lime from the tap itself, no bottle in sight. The interactive moment enacts the push-and-turn safety dial. The closing line asks the visitor to make room.

## 2. The palette as CSS tokens

Dark warm edition, owner's brief: "a Gessi styled theme, minimal luxury, dark warm tones". Espresso darks sampled from the film's shadows, warm ivory type, brushed bronze in rare doses (the active point, the strike lines, the safety dial, the final buy button).

```css
:root{
  --canvas:#14100D;        /* espresso, never pure black */
  --canvas-2:#1A1511;      /* alternate band for rhythm */
  --panel:#221B16;
  --hair:rgba(236,227,214,.14);
  --text-primary:#ECE3D6;  /* warm ivory, 14.8:1 on canvas */
  --text-secondary:#A69A8C;/* 6.9:1 on canvas */
  --accent:#C4A57D;        /* brushed bronze, 8.1:1 on canvas */
  --on-accent:#14100D;
}
```

This is the "near-black with a warm accent" family the skill warns against as a default reach; it is used here because the owner asked for it, kept honest by sampling every tone from the footage and keeping the accent rare.

## 3. The type

One family, Jost (200, 300, 400), a light Italian-geometric sans in the spirit of Gessi's "design sans". Display at 200 with slight negative tracking, body at 300, and small spaced capitals (0.28em) as the house label in place of a mono. A deliberate deviation from the three-face default: one family carries the quiet, monolithic voice of the brand.

## 4. The band map

Concept (current, the owner's own footage): in a warm, backlit kitchen a hand reaches in, pushes and turns the Farless handle, and sparkling water pours into a glass of ice and lime while she smiles. One continuous 8-second shot.

Interaction (owner's request): the film fills the whole first screen and moves point to point. One scroll gesture, swipe or arrow key plays the film on to the next point and stops; scrolling up steps back. A column of dots on the right edge marks the points (current one larger and darker) and each dot jumps to its point. After the last point the page scrolls on normally; returning to the top shows the last point.

| Point | Film time | Footage moment | Copy (verbatim) | Entrance |
|---|---|---|---|---|
| 1 | 0.0s | Hand resting by the glass of ice and lime | "Farless." / "Five waters. One tap." | Blur-to-sharp (plays on load) |
| 2 | 2.8s | Her hand on the handle, mid push and turn | "Boiling. Filtered." | Drift-down |
| 3 | 4.6s | The stream runs into the glass | "Sparkling. Hot. Cold." | Drift-down |
| 4 | 6.4s | The glass fills, she leans in | "No kettle. No bottles. No soda machine." | Drift-down |
| 5 | end | At rest: the glass full, she smiles | "Far less on your counter." / "Just one tap." / button "Buy Farless" | Word rise into a staged settle |

Layout: captions sit bottom-left in a column that ends before the glass, light text over a bottom-left shade plus a local shade behind each caption (worst-pixel contrast at least 4.1:1 at every point and size). The video frames at object-position 20% so the faucet and glass sit a little right of the text. Palette warmed toward the footage: canvas #EFE8DF, panel #F8F3EC, text #26211D, secondary #5B524A, accent mineral blue #24505C.

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
   - Confirmed by the owner: the knob only turns once the pin is pressed down (safety section copy stands), and the questions answer keeps "boiling" water for push and turn.
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
