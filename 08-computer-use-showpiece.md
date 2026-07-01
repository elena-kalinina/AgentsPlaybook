# 08 — Computer-Use Showpiece (the single live flourish)

ONE bet, placed live by driving the real Cup Clash UI on stage. This is theatre. It must never be load-bearing: the tool-layer `place_bet` (`03-mcp-tools.md`) is the silent fallback, and the rest of the demo (replay) already told the whole story without it.

## Two implementations (build the first, optionally add the second)

### A. Playwright (primary — reliable)
Deterministic selectors against the betting screen. From the current UI, the flow for a match card is:

1. On the match card, click **"I'M IN"** (if not already joined).
2. Click **"Place your bet"** to expand the form.
3. **WINNER:** click one of the three toggles — `Panama` / `Draw` / `England` (use the team-name text or a stable `data-` attribute; prefer adding `data-testid` hooks in the app, see below).
4. **PREDICTED SCORE (optional):** fill the two number inputs (home / away).
5. **YELLOWS / REDS:** set the two number inputs.
6. **FAVOURITE PLAYER (optional):** type into the text field.
7. Click **"Lock it in"**.
8. Assert the bet now shows as locked (the "x/6 bets placed" count increments / the card shows the agent's locked state).

Map the agent's chosen prediction to these fields, run with a visible browser and a slowed `slowMo` so the audience sees the cursor move. Take a screenshot before "Lock it in" for the recap.

> **Make it robust:** add `data-testid` attributes to the app's bet controls (a tiny, additive UI change in Cup Clash) so selectors don't depend on visible text or layout. e.g. `data-testid="winner-home|draw|away"`, `"input-yellows"`, `"input-reds"`, `"input-favplayer"`, `"lock-in"`. This is the difference between a reliable showpiece and a flaky one.

### B. Claude computer-use (optional — flashier, riskier)
The vision-driven variant: give a computer-use model a screenshot + the instruction "place this bet" and let it find and click controls itself. More impressive as a story ("it's reading the screen like a person"), much more likely to stall or misclick live. If you build it, keep Playwright (A) as a one-keypress fallback and rehearse the handoff.

## Live-fallback pattern

```
try {
  await showpiece.placeBetViaUI(agent, match, prediction);  // Playwright (or computer-use)
} catch (e) {
  log('showpiece failed, falling back to MCP', e);
  await tools.place_bet({ agent_id, match_id, prediction_id });  // silent, always works
  toast('placed via API fallback');
}
```

The audience either sees the cursor place the bet, or sees the bet appear "instantly via the API" — both are fine outcomes. There is no failure state where the demo dies.

## What to pick for the live bet

Use a genuinely upcoming match (e.g. tonight's game) and the **Contrarian** or **Pundit** agent, because their reasoning is the most fun to narrate while the cursor moves. Show the agent's written reasoning on one side of the screen and the browser placing the bet on the other.

## Safety

This drives only the Cup Clash app to place a play-money, points-only prediction. It must not navigate to, log into, or interact with any real betting site, payment page, or anything outside the Cup Clash domain. Restrict the browser context to `CUP_CLASH_BASE_URL`.

## Rehearsal checklist

- [ ] `data-testid` hooks added to the app and selectors pinned to them.
- [ ] Visible browser + `slowMo` tuned so it reads on a projector.
- [ ] Fallback path tested by deliberately breaking a selector.
- [ ] A pre-recorded screen capture of a clean run saved as the ultimate backup.
- [ ] Agent login session is pre-authenticated (no live password typing on stage — and never automate credential entry).
