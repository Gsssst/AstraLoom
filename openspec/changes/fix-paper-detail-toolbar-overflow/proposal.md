## Why

Long paper titles can overlap the reading status controls in the paper detail toolbar, and the rightmost favorite button can be clipped. This makes the paper page hard to use for papers with long titles.

## What Changes

- Constrain the paper detail title area so it ellipsizes instead of pushing toolbar actions.
- Add a dedicated toolbar actions container that can wrap or shrink safely.
- Ensure the favorite button and action groups remain fully visible.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The paper detail toolbar remains readable and usable with long paper titles.

## Impact

- Frontend paper detail page markup and responsive styles.
- Frontend contract test for toolbar overflow behavior.
