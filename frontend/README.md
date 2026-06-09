# AstraLoom Frontend

This package contains the AstraLoom web client.

## Stack

- React 19
- TypeScript
- Vite 8
- Ant Design 6
- React Router
- Zustand
- Axios
- react-markdown with GFM and KaTeX
- react-pdf / pdfjs-dist

## Local Development

Install dependencies:

```bash
npm install
```

Run the Vite dev server:

```bash
npm run dev
```

The dev server usually runs at:

```text
http://localhost:5173
```

The frontend expects the backend API to be reachable through the configured Vite API base URL or the local proxy used by the current development setup.

## Build

```bash
npm run build
```

Preview a production build:

```bash
npm run preview
```

## Contract Tests

Focused frontend contract tests live in `frontend/tests/` and can be run with Node's built-in test runner. Examples:

```bash
node --test tests/app-layout-contract.test.mjs
node --test tests/research-toolbox-contract.test.mjs
node --test tests/writing-workbench-contract.test.mjs
```

## App Areas

The main routes are defined in `src/App.tsx` and lazy-loaded through `src/routes/lazyRoutes.tsx`.

- `/chat`: AI chat, RAG, web search, uploads, reasoning display.
- `/papers`: paper library search, import, markers, reports.
- `/toolbox`: reusable research tools, methods, datasets, metrics, and protocols.
- `/research`: evidence-grounded idea generation and proposal review.
- `/writing`: section-based LaTeX writing and AI writing assistance.
- `/workspaces`: lab project spaces, resources, members, feedback issues.
- `/settings`: profile, language, API configuration display, usage, subscriptions.
- `/admin`: admin governance surfaces.

## UI Notes

- The app shell supports Simplified Chinese and English through `src/i18n/`.
- Business page copy is still mostly Chinese and should be migrated incrementally when touching related pages.
- Prefer existing components and Ant Design patterns before adding new abstractions.
- Keep dense research workflows readable: stable dimensions, clear next actions, and no decorative page shells that reduce workspace width.
