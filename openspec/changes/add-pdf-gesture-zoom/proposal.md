## Why

The previous local loupe zoom does not match the expected PDF-reader interaction. Users want the PDF pane to behave like a normal viewer: pinch on a touchpad, use Ctrl/Cmd + wheel, or click toolbar zoom controls to enlarge the whole rendered page while keeping the reading position stable.

## What Changes

- Replace the toggleable local PDF magnifier with global page zoom in the enhanced PDF reader.
- Add toolbar controls for zoom out, zoom percentage, zoom in, and fit-to-width reset.
- Support touchpad pinch / Ctrl-or-Cmd wheel zoom inside the PDF scroll area.
- Preserve the cursor-centered reading position as much as possible while changing zoom.
- Keep text selection, evidence highlighting, page tracking, and native PDF fallback behavior intact.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The PDF reader supports global gesture and toolbar zoom for rendered PDF pages without disrupting evidence-aware reading workflows.

## Impact

- Frontend PDF viewer component and responsive styles.
- Frontend contract test for global PDF zoom behavior.
- Removes the superseded local magnifier implementation and its unarchived OpenSpec change.
