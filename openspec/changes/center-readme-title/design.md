## Context

The README already uses centered HTML paragraphs for tagline, navigation, and badges. The top Markdown heading remains left-aligned on GitHub, which makes the hero block feel visually inconsistent.

## Decision

Use a simple HTML heading:

```html
<h1 align="center">AstraLoom</h1>
```

This is supported by GitHub Markdown rendering and preserves the heading semantics closely enough for a repository README.

## Non-Goals

- No logo redesign.
- No README content rewrite.
- No changes to app branding or runtime UI.

## Validation

- Run OpenSpec validation.
- Run `git diff --check`.
