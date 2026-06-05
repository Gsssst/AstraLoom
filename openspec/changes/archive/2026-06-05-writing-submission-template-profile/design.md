# Design: Writing Submission Template Profile

## Approach

Use project metadata as the first storage surface:

```json
{
  "submission_profile": {
    "venue": "CVPR",
    "year": "2026",
    "template_source": "cvpr2026_author_kit.zip",
    "template_status": "inspected",
    "document_class": "article",
    "class_files": ["cvpr.sty"],
    "warnings": []
  }
}
```

This avoids a premature template database while allowing the writing workbench to become venue-aware.

## Template Inspection

The inspector accepts:

- `.tex`: parse documentclass, packages, bibliography, sections.
- `.cls` / `.sty`: record class/style files and likely venue signals.
- `.zip`: inspect a bounded number of text-like LaTeX files using Python `zipfile`; ignore binary/large files.

The output includes a confidence/status and warnings such as missing `\documentclass`, no main `.tex`, or no style/class files.

## UI

The writing project export panel gets a "投稿目标与模板" area:

- venue/year inputs
- upload official template file or zip
- inspection summary
- bind profile to current project
- explicit warning that built-in structure templates are not official submission formatting

## Future Work

- Store template bundles as managed artifacts.
- Render project LaTeX through selected template files.
- Run compile checks with imported `.cls/.sty`.
- Add venue-specific writing checklist.
