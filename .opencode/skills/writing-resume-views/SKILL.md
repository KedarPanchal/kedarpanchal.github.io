---
name: writing-resume-views
description: Use when creating or editing a tailored resume view YAML file for this repo (files like resume.view.yaml or *.view.yaml passed to `uv run render -r`). Covers the include/exclude filter DSL that selects fields from data.yaml, its ordering rules, and the integer-vs-string indexing constraint.
---

# Writing resume view YAML files

A view file is a **filter**, not data. It names top-level keys from `data.yaml`
and, for each, selects or trims what gets rendered. The resume renderer only
reads from `data.yaml` through the view you pass with `-r`
(default `resume.view.yaml`).

## Workflow for tailoring a resume

1. **Never edit `data.yaml`.** It is the single source of truth for all
   content. Tailoring is done purely by creating new view files that filter it.
   Do not add, remove, or reword anything in `data.yaml`.
2. **Create a new view file in `tailored-resumes/`.** Copy `resume.view.yaml`
   as a starting point, give it a descriptive name
   (e.g. `tailored-resumes/acme-backend.view.yaml`), and adjust the
   include/exclude lists. Create the folder if it does not exist.
3. **Build the resume by invoking `uv`:**

   ```
   mkdir -p dist/resume dist/site
   uv run render -m r -r tailored-resumes/acme-backend.view.yaml
   ```

   This writes `dist/resume/resume.tex`. Produce the PDF with
   `scripts/render_resume.sh` if needed.

## The source shape (`data.yaml`)

Top-level keys the resume renderer *requires* (see `latex_renderer.py` — it
unconditionally reads all of these, so a resume view must keep them all):

- `name` — string
- `info` — object: `email, phone, website, github, hugging-face, linkedin, miscellaneous[]`
- `education` — object: `university, degree, location, start, end, gpa, courses[]`
- `experience` — **list** of objects: `title, company, location, start, end, bullets[]`
- `projects` — **list** of objects: `title, start, end, url, bullets[]`
- `skills` — object: `languages[], frameworks[], tools[]`
- `certifications` — **list** of strings

Omitting a required key from a resume view will crash the LaTeX renderer with
an `AttributeError`. Only trim *within* a section, don't drop whole sections a
resume needs.

## Filter DSL (implemented in `yaml_parser.py`)

Each top-level key maps to either nothing (keep whole field) or an object with
`include` and/or `exclude`.

```yaml
name:                 # bare key = include everything unchanged

info:                 # same — null value means "keep all"

education:
  include:            # keep only these sub-keys...
    - university
    - degree
    - courses:        # ...and recurse: nested include/exclude on courses[]
        exclude:
          - Programming Languages   # drop these list ITEMS by value

experience:
  include:            # LIST indices — keeps entries 0,1,2 in this order
    - 0
    - 1
    - 2

skills:
  include:
    - languages:
        exclude:
          - Haskell   # drop a value from the languages[] list
    - frameworks
    - tools

certifications:
  include:            # pick specific certs by index
    - 2
    - 3
    - 4
```

### Rules that are easy to get wrong

- **Never mix integer indices and string keys under one `include`.** A list of
  ints indexes into a source list (result is a list); a list of strings/dicts
  selects dict keys (result is a dict). Mixing raises
  `"Cannot mix indexing and non-indexing snapshots"`.
- **`include` ordering is preserved.** For list sections (`experience`,
  `projects`, `certifications`) the output order follows the index order you
  write, not the order in `data.yaml`. Reorder entries by reordering indices.
- **`exclude` removes by value for lists, by key for dicts.** Integer excludes
  on a list are resolved to the value at that index, then that value is
  filtered out.
- **Nested filtering** uses a one-key mapping inside the `include` list, e.g.
  `- courses: { exclude: [...] }`. The key must exist in the source or it
  raises `"Item '<x>' not found"`.
- `include: all` (or omitting `include`) keeps the whole field;
  `exclude: all` drops it entirely (yields null).
- A missing string key in `include` raises; a missing top-level key just
  yields null and is skipped. Keep required resume keys present.
- Top-level view values must be either null or a mapping — not a scalar/list
  directly (`"Top-level values in the view file must be fields."`).

## Verify

List indices are positions in `data.yaml`, so confirm them against the current
`data.yaml` (read it, don't edit it). Run
`uv run render -m r -r tailored-resumes/<view>` and inspect
`dist/resume/resume.tex`; the INFO log prints the filtered `SimpleNamespace`
so you can confirm what survived the filter. Build the PDF with
`scripts/render_resume.sh`.
