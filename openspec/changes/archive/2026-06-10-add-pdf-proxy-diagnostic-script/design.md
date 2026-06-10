## Context

The PDF preview path depends on a URL such as `/api/papers/pdf-proxy/<arxiv_id>`. When a browser preview times out but direct PDF access may or may not work, the fastest next step is to measure the deployed endpoint from the server or an operator machine.

## Decisions

- Use only Python standard library modules so the script runs on most Linux servers without installing dependencies.
- Test both regular and `Range` requests because pdf.js can use partial-content behavior.
- Read only a bounded sample of the PDF by default to avoid downloading very large files unnecessarily.
- Print key headers and a simple diagnosis rather than only raw HTTP output.

## Non-Goals

- Fixing PDF preview directly.
- Modifying backend routes or nginx config.
- Replacing browser DevTools inspection.
