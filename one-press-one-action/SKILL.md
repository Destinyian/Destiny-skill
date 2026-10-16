---
name: one-press-one-action
description: Use when a single click or tap produces two effects — "the toggle undoes itself", "click fires twice", "it collapses and instantly restores" — or when a gesture handler is shared by several pointer events. The idea: one physical press emits several events (pointerup plus lostpointercapture, sometimes pointercancel), so routing them all to one handler without a state guard makes every press act twice.
---

# One physical press must produce exactly one action

**The idea.** A press is not one event. The browser delivers `pointerup` **and**
`lostpointercapture`, and sometimes `pointercancel`, for the same finger or button release. If all of
them reach the same action, the action runs more than once — which the user experiences as "it does
nothing", because the effect and its undo cancel out within one frame.

**Where it came from.** A drag-to-collapse component whose single click "did not work". The click
handler was correct; it simply ran twice per press, so the collapse fired and was immediately
reversed. It was reproduced only after dispatching input through the real pipeline
(`Input.dispatchMouseEvent`) instead of synthetic `pointerdown`/`pointerup` pairs.

**Recall it when.** A toggle appears to do nothing; an animation runs and snaps back; a state flag
flips twice in one frame; a handler is registered for several event types at once; tests pass with
synthetic events but the real UI misbehaves.

## How to apply

1. **Guard on state, not on event type.** Every release-ish event checks the same flag and clears it:

   ```js
   function onPointerUp(ev) {
     if (pointer.id === -1) return;   // already handled this press
     pointer.id = -1;
     release();
   }
   el.addEventListener('pointerup', onPointerUp);
   el.addEventListener('lostpointercapture', onPointerUp);
   el.addEventListener('pointercancel', onPointerUp);
   ```
2. **Count it.** Log or expose a counter of actions per press; assert it is 1. An off-by-one here is
   invisible in a screenshot and obvious in a counter.
3. **Separate press from drag with an explicit threshold**, and suppress the click for ~300 ms after
   a drag so a wipe does not also trigger the action.
4. **Test through the real input pipeline.** Synthetic `down`/`up` pairs never produce a stray
   `lostpointercapture`, so they cannot reproduce this class of bug at all — dispatch real mouse
   events, including a few pixels of drift while the button is down.

## Boundaries

If the element never takes pointer capture, `lostpointercapture` will not fire and the guard is
harmless but unnecessary; keep it anyway, because capture is added the moment someone implements
dragging. On touch, a second `pointerdown` with a different `pointerId` is a genuinely new press —
never dedupe across different ids, or pinch and multi-touch break.

## Evidence

| Symptom | Cause | Counter after the guard |
|---|---|---|
| click collapses then restores within one frame | `pointerup` + `lostpointercapture` both ran the action | 1 action per press |
| click ignored after a hover-wipe | 6 px drag threshold while the button was down (real mice drift 10–30 px) | click fires; drag still suppresses it |
| "click does nothing" reported by the user, not reproducible by synthetic events | synthetic events omit `lostpointercapture` | reproduced with `Input.dispatchMouseEvent` + drift |

## Verify

```js
// dispatch one real press with drift and assert the counter
await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
await client.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: x + 12, y });   // real drift
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: x + 12, y, button: 'left', clickCount: 1 });
// expect: actions === 1
```

If the counter is 1 with synthetic `pointerdown`/`pointerup` but 2 with real input, the guard is
missing — the synthetic path is the one that cannot fail.
