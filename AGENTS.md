# AGENTS.md

## What this repo is

A personal resume + portfolio-site generator, not a hand-written site. A single source of truth (`data.yaml`) is filtered through "view" files and rendered by Python (`src/render/`) into:
- a LaTeX resume (`dist/resume/resume.tex` -> PDF via `pdflatex`)
- Jekyll markdown pages (`dist/site/rendered_*.md`), copied into `site/` and built by Jekyll.

To change resume/site *content*, edit `data.yaml`. To change what's *shown*, edit the view files. To change *formatting*, edit the renderers.

Agent skills live in `.agents/skills/` (`writing-resume-views`, `writing-cover-letters`). They depend on skills supplied by the user's dotfiles repo — `pdf-handling`, `humanizer`, and the `tavily` CLI — so those workflows need that environment; plain rendering does not.

## Commands

- Render both resume + site: `uv run render` (writes to `dist/resume/` and `dist/site/`; both dirs must exist first — `mkdir -p dist/resume dist/site`).
- Flags: `-m r|s|rs` (resume only / site only / both, default both; `sr` is also accepted), `-r <path>` (resume view file, default `resume.view.yaml`).
- Full local resume build (render + PDF): `scripts/render_resume.sh` (runs `uv run render -m r`, so it makes no network calls).
- Full local site build (render + copy into `site/` + serve): `scripts/render_site.sh` (runs `uv run render -m s`; needs Ruby/Bundler + Jekyll in `site/`).
- Each script renders only its own output, so the resume script neither writes `dist/site` nor hits the network.

There are no tests, linters, or typecheck configs. Verify changes by running `uv run render` and inspecting generated output. Note: the Python has `# type: ignore` hints but no checker is configured.

## Key gotchas

- **Argparse runs at import time.** `src/render/__init__.py` calls `arg_parser.parse_args()` at module top level, so importing the package parses `sys.argv`. Keep CLI usage going through `uv run render`.
- **Hardcoded paths.** The parser always reads `data.yaml` and `site.view.yaml` from CWD, and writes to `dist/resume/resume.tex` / `dist/site`. Run from repo root.
- **Network call during site render.** `JekyllRenderer._get_opengraph_url` fetches each project's `url` to scrape its `og:image`, falling back to a placehold.co image. Site rendering requires network and hits external sites.
- **View files are filters, not data.** `*.view.yaml` select/trim fields from `data.yaml` via `include`/`exclude`: string keys address mapping fields, integer indices address list entries, and `include: all` (or no `include`) keeps a field whole. Mixing integer indices and string keys in one `include` does not raise — the indexed entries are silently dropped. `exclude` on a list only takes non-negative integer indices; item values and negative indices are ignored there. `resume.view.yaml` and `site.view.yaml` can differ (e.g. resume excludes some courses/skills). The README documents the full DSL.
- **LaTeX escaping lives in `latex_renderer.py`.** `escape_latex` escapes `\ & % $ # _ { } ~ ^` and is applied to every field the resume renderer prints; add it to any new field you render.
- Generated outputs (`dist/`, `site/rendered_*`, `site/_site`) are gitignored — don't commit them. The contents of `tailored-resumes/` and `cover-letters/` are gitignored too; only their `.gitignore` files are tracked.

## CI (`.github/workflows/render.yaml`)

A push to `main` starts the workflow when it touches one of the `on.push.paths` entries: `data.yaml`, `resume.view.yaml`, `site.view.yaml`, `src/render/renderer.py`, `src/render/latex_renderer.py`, `src/render/jekyll_renderer.py`, `site/**`, or the workflow itself.

Once triggered, `dorny/paths-filter` decides whether to rebuild the resume, the site, or both:
- resume: `data.yaml`, `resume.view.yaml`, `renderer.py`, `latex_renderer.py`, the workflow
- site: `data.yaml`, `site.view.yaml`, `renderer.py`, `jekyll_renderer.py`, `site/**`, the workflow

The resume PDF is built in a `texlive` container and published as a dated GitHub Release; the Jekyll site deploys to GitHub Pages.
