# AGENTS.md

## What this repo is

A personal resume + portfolio-site generator, not a hand-written site. A single source of truth (`data.yaml`) is filtered through "view" files and rendered by Python (`src/render/`) into:
- a LaTeX resume (`dist/resume/resume.tex` -> PDF via `pdflatex`)
- Jekyll markdown pages (`dist/site/rendered_*.md`), copied into `site/` and built by Jekyll.

To change resume/site *content*, edit `data.yaml`. To change what's *shown*, edit the view files. To change *formatting*, edit the renderers.

## Commands

- Render both resume + site: `uv run render` (writes to `dist/resume/` and `dist/site/`; both dirs must exist first — `mkdir -p dist/resume dist/site`).
- Flags: `-m r|s|rs` (resume only / site only / both, default both), `-r <path>` (resume view file, default `resume.view.yaml`).
- Full local resume build (render + PDF): `scripts/render_resume.sh`.
- Full local site build (render + copy into `site/` + serve): `scripts/render_site.sh` (needs Ruby/Bundler + Jekyll in `site/`).

There are no tests, linters, or typecheck configs. Verify changes by running `uv run render` and inspecting generated output. Note: the Python has `# type: ignore` hints but no checker is configured.

## Key gotchas

- **Argparse runs at import time.** `src/render/__init__.py` calls `arg_parser.parse_args()` at module top level, so importing the package parses `sys.argv`. Keep CLI usage going through `uv run render`.
- **Hardcoded paths.** The parser always reads `data.yaml` and `site.view.yaml` from CWD, and writes to `dist/resume/resume.tex` / `dist/site`. Run from repo root.
- **Network call during site render.** `JekyllRenderer._get_opengraph_url` fetches each project's `url` to scrape its `og:image`, falling back to a placehold.co image. Site rendering requires network and hits external sites.
- **View files are filters, not data.** `*.view.yaml` select/trim fields from `data.yaml` via `include`/`exclude` (string keys, integer list-indices, or `all`). You *cannot* mix integer indices and string keys under one `include`. `resume.view.yaml` and `site.view.yaml` can differ (e.g. resume excludes some courses/skills).
- **LaTeX escaping is manual and partial.** Renderers only escape a few chars (`&`, `%`) in specific fields. New special LaTeX chars in `data.yaml` can break the PDF build.
- Generated outputs (`dist/`, `site/rendered_*`, `site/_site`) are gitignored — don't commit them.

## CI (`.github/workflows/render.yaml`)

Pushes to `main` trigger render only when relevant paths change. `dorny/paths-filter` decides whether to rebuild resume vs site independently:
- resume path split: `latex_renderer.py` + resume inputs
- site path split: `jekyll_renderer.py` + `site/**` + site inputs

Resume PDF is built in a `texlive` container and published as a dated GitHub Release; the Jekyll site deploys to GitHub Pages. Editing `renderer.py` or the workflow triggers both.
