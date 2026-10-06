# Keypoints

Talking points per slide, not a script. Extra context I've decided *not* to put
on the slide itself (too dense) but should still say out loud is marked
**(say, not on slide)**.

---

### 1. Title
- Seminar project done before my master's thesis.
- One-liner: can zero-shot vision-language models classify American football pre-snap
             formations from amateur broadcast footage?

### 2. Outline
- Quick structural map: Motivation → Background → Data & Methods →
  Results → Discussion & Conclusion.

### 3. Why automate formation tagging?
- Football is "chess on the field": pre-snap formation tells coaches a lot
  about the play tactically.
- At the amateur level (Austrian Football League), this tagging is done
  entirely by hand on platforms like Hudl.
- Small clubs have no staff to dedicate to film review.
- Open-weight VLMs can run locally, cheaply - could they help?

### 4. Research Questions
- RQ1: can user-grade open-source VLMs identify formations zero-shot?
- RQ2: how do the three models (Qwen-VL, Gemma, LLaMA) compare?
- RQ3: what are the main failure modes on amateur-quality footage?
- rest of the talk answers RQs

### 5. What a pre-snap formation shows
- Four visual cues define a formation: backfield occupied or empty, WR count
  per side, TE/FB on the line or not, which side has the extra receiver
  ("strong side").
- Why it's hard: needs precise counting + spatial reasoning — easy to miss
  even for a person on grainy broadcast footage.

### 6. The Formation Classes (1/2)
- EMPTY: no RB/FB, QB alone in the backfield.
- TRIO: 3 WR one side, 1 WR the other side, RB in the backfield, **no TE**.
- DOUBLES: balanced 2 WR + 2 WR, RB in the backfield.

### 7. The Formation Classes (2/2)
- TREY: same skeleton as TRIO, but with a TE/FB aligned on the **strong**
  (3-receiver) side.
- TANK: same skeleton as DOUBLES, but with a TE/FB aligned on the **weak**
  (1-receiver) side.
- Point out: TRIO/TREY and DOUBLES/TANK are minimal pairs — visually and
  semantically close. This is exactly where the models later get confused.

### 8. Four Games, Four Different Cameras: Up Close
- Game 3 and Game 1 — the two closer/lower camera angles.

### 9. Four Games, Four Different Cameras: From Further Away
- Game 2 and Game 4 — the two more elevated, further-back camera angles.
- 4 different broadcast setups — camera angle and distance differ a lot.

### 11. Dataset
- 40 offensive plays across 4 AFL games, one pre-snap frame per play.
- Manually annotated: formation, play type, jersey colors, offense side.
- Majority class TRIO at 35%

### 12. Models Under Test
- Three open-weight VLMs, all served locally via Ollama on a single 24GB GPU.
- 30B / 27B / 11B parameters, all 4-bit quantized.
- Deterministic decoding (temperature=0) and fully zero-shot

### 13. Evaluation Protocol
- Three-phase design:
- Phase A is text-only (do the models even know the formation *names*, with no image at all?);
- Phase B is basic image understanding (sanity checks: colors, sides, counts);
- Phase C is the actual classification task, tested under four prompting strategies.
- Majority baseline: 35.0%

### 14. Phase C: Four Prompting Strategies
- C1: bare baseline, image + class names only.
- C2: + a natural-language description per class.
- C3: + an explicit step-by-step decision tree.
- C4: + just an explicit vocabulary correction (nothing else added).
- C4 exists specifically to test something found in Phase A — flag that
  connection here, pay it off later.

### 15. Pipeline Overview
- ffmpeg pulls the pre-snap frame out of the broadcast clip
- frame goes to the local VLM via Ollama with the phase-specific prompt
- response gets regex-parsed into a label 
- accuracy computed from that.

### 16. Phase A: Inconsistencies, Before Any Image (1/2)
- Walk the table row by row:
  - A2 (name EMPTY): all three correct.
  - A3 (which formations use a TE/FB): only Gemma correct.
  - A4 (name the 3-WR-one-side formation, i.e. TRIO): all three wrong. all had trey
  - A5 (name DOUBLES): Qwen and Gemma correct, LLaMA wrong.
  - A6 (TRIO vs. TREY, explain the difference): all three wrong.
  - A7 (DOUBLES vs. TANK, explain the difference): all three wrong.

### 17. Phase A: Inconsistencies, Before Any Image (2/2) — Finding

- EMPTY as a standardized football terminology
- other fomations are not standardized. 

### 18. Phase B: Basic Image Understanding
- check the fundamentals: can the models even read the image reliably?
- Five things tested here: basic sanity checks (jersey colors, offense
  side, player counts/WR counts, QB stance and RB in backfield); 
- are the models even answering consistently; 
- swap analysis (offense/defense role confusion);
- and whether telling the model the offense side
  explicitly (Phase B2) fixes anything (spoiler, coming up: it doesn't).

### 19. Phase B: Results (1/2)

- these are the basic sanity-check questions: "can the model read the image at all."
- on WR count / RB visible specifically:
  - Qwen scores 0% on WR count outright.
  - Gemma's 88% on RB-visible and 25% on WR-count look
    decent until you see the raw answers: Gemma answers "3 wide receivers,
    yes RB" on all 40 images, correct only when the ground truth happens to be 3.
  - LLaMA answers "no RB" on all 40 images.
- swap table: "Swapped" specifically means the model named the
  *defense's* actual color when asked for the offense's — a literal
  role-confusion, not just a random wrong guess. Even when we hand the
  model the answer to "which side is offense," the majority of
  jersey-color errors are still these literal swaps (54%).
- Further:
  - Qwen's empty-response rate specifically: 40% on Games 2 & 4 vs. 20% on
    Games 1 & 3 — tied to which camera/broadcast setup was used, not
    evenly spread across the dataset. The further players away the harder for the model to generate an answer.
  - This camera-angle effect isn't limited to player counts: accuracy on
    every Phase B question varies by game too, e.g. Qwen's offense-side
    accuracy ranges 30%–70% across the 4 games — "40 images" isn't really
    40 independent draws from one distribution.

### 20. Phase B: Results (2/2) — Finding
- On-slide: just the headline — basic image reading is inconsistent, and
  often not really "reading" at all.+
- three supporting points
  1. Gemma answers "3 WR / Yes RB" on all 40 images, LLaMA answers "No RB"
     on all 40 - constant answers, not per-image judgments. 
     "we're going to see this same pattern again - a model outputting one fixed answer
     regardless of the image, not actually perceiving anything per-image."
     That's the thread connecting Phase B to Phase C's collapse.
  2. Qwen's empty responses track camera angle, not random noise — a
     documented limitation, not retried (temp=0 is deterministic).
  3. Most jersey-color errors are literal offense/defense swaps even with
     the side given (65%→54%), and giving the side away mostly makes
     other metrics worse.

### 21. Code Walkthrough
- Everything lives in `evaluation.ipynb`: the Ollama API call and the C1–C3
  prompt definitions specifically.
- Say why it's placed here now: this is the code behind the Phase C
  prompting strategies you're about to see the results of, so it sits
  right before them instead of back with the general pipeline.

### 22. Phase C: Formation Classification Accuracy
- On-slide: accuracy per model × phase (C1–C4) with 95% CI (±9–15pp,
  binomial approximation, n=40 per cell).
- Say: the ± number is the margin of error on each accuracy estimate from
  having only 40 samples per cell — if 1.96×SE is added/subtracted from
  the point estimate, you get a range the true accuracy would fall in
  ~95% of the time under repeated sampling. It's there so the room doesn't
  over-read small differences: e.g. Qwen's C1→C2 jump (10.0%→30.0%) looks
  big, but the intervals [1,19] and [16,44] actually overlap — so we can't
  confidently call that a real improvement from this data alone.

### 23. Phase C: Models Default, They Don't Classify
- On-slide: ground-truth % vs. predicted % per formation across all 480
  Phase C predictions; TREY over-predicted 3.7×, EMPTY almost never
  guessed (0.1×).
- Say: across all 3 models × 4 phases × 40 images, TREY is the models'
  generic fallback guess — only actually correct 12.5% of the time, but
  chosen 46.5% of the time. EMPTY is the mirror image: true 12.5% of the
  time, guessed almost never. This is the single-label-collapse pattern
  shown at the formation level, aggregated across all of Phase C


### 26. Why It's Not Working (1/2): Terminology
- On-slide: football terminology isn't standardized, so pretrained models
  bring in a naming prior
- Evidence: Questions from phase A

### 27. Why It's Not Working (2/2): Perception
- On-slide: offense-side identification is barely above chance (45–50%);
  WR count is 0% (Qwen) / 15% (LLaMA) / 25% (Gemma, but via a constant
  answer, not counting); RB-in-backfield is dominated by LLaMA's constant
  "No" (12% correct, only right on the truly-empty images).
- this is the second, root cause:
  - even before formation vocabulary matters at all, the models often aren't reliably extracting
    the basic facts the formation decision depends on: 
    - hwo's on offense,
    - how any receivers,
    - is there a back in the backfield.
- Two failure modes, not one — terminology confusion on top of a shaky perceptual foundation.

### 28. Limitations
- small test set (40 images, 5 per minority class)
- single competition/league;
- 4-bit quantization;
- purely zero-shot.

### 29. Conclusion RQ1 & RQ2
- 1. POINT
   - two conditions beat baseline but within a ±15pp CI;
   - every condition collapses onto one or two dominant labels;
- 2. point 
   - no real multi-class discrimination;
   - peak accuracy doesn't track parameter count.

### 30. Conclusion RQ3
- RQ3 asked for the main failure modes
1. Terminology isn't standardized
2. offense-side identification is barely above chance, and WR-count/RB-in-backfield answers are often a constant,
        not a per-image judgment

### 31. Future Work
- few-shot prompting with corrected examples;
- fine-tuning on a larger multi-league dataset;
- block on the master's thesis CV pipeline.

### 32. Thank You / Questions

