# Resume + Site Generator

A personal resume and portfolio-site generator. A single source of truth, `data.yaml`, is filtered through "view" files (`resume.view.yaml`, `site.view.yaml`) and rendered by Python into:

- a LaTeX resume (`dist/resume/resume.tex`, compiled to a PDF with `pdflatex`)
- Jekyll markdown pages (`dist/site/rendered_*.md`, copied into `site/` and built by Jekyll)

To change resume/site *content*, edit `data.yaml`. To change what's *shown*, edit the view files. To change *formatting*, edit the renderers in `src/render/`.

## Table of contents

- [Project layout](#project-layout)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [`data.yaml`](#data-yaml)
- [View files](#view-files)
- [CI](#ci)

## Project layout

```
.
├── data.yaml                       # single source of truth: all content
├── resume.view.yaml                # default resume filter (the -r target)
├── site.view.yaml                  # Jekyll site filter
├── src/render/
│   ├── __init__.py                 # CLI entry point (argparse, `render` command)
│   ├── parser.py                   # loads data.yaml, applies a view, yields a namespace
│   ├── renderer.py                 # Renderer ABC
│   ├── latex_renderer.py           # writes dist/resume/resume.tex
│   └── jekyll_renderer.py          # writes dist/site/rendered_*.md
├── scripts/
│   ├── render_resume.sh            # render + pdflatex
│   └── render_site.sh              # render + copy into site/ + jekyll serve
├── site/                           # Jekyll site: theme, layouts, includes, assets, Gemfile
├── tailored-resumes/               # job-specific resume views and their PDFs (contents gitignored)
├── cover-letters/                  # generated cover letters (contents gitignored)
├── pyproject.toml, uv.lock         # Python project + pinned dependencies
├── .python-version                 # pinned Python version
├── LICENSE
├── AGENTS.md                       # contributor notes for agents
└── .github/workflows/render.yaml   # CI: render, build, release, deploy
```

Every path above is tracked in git; the contents of `tailored-resumes/` and `cover-letters/` are gitignored, so only the folders and their `.gitignore` files are committed. Generated output such as `dist/` is gitignored entirely and is created by the commands in [Usage](#usage) rather than listed here.

## Dependencies

My [dotfiles repo](https://github.com/KedarPanchal/dotfiles) is **required** for this project: it sets up the environment below and installs the agent skills that the skills in `.agents/skills/` reference. Without it, rendering still works, but the tailoring and cover-letter workflows break at their skill-dependent steps.

**Core**

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management and running the `render` command

**Python packages** (declared in `pyproject.toml`, locked in `uv.lock`)

- [PyYAML](https://pyyaml.org/) — parses `data.yaml` and the view files
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) — scrapes project pages for Open Graph images
- [requests](https://requests.readthedocs.io/) — HTTP client used by that scraping

**Resume build**

- A LaTeX distribution providing `pdflatex` (TeX Live in CI)

**Site build**

- Ruby with Bundler
- Jekyll 4.4 plus the `jekyll-theme-hydejack`, `minima`, and `jekyll-feed` gems (see `site/Gemfile`)

**Agent skills** (provided by the dotfiles, referenced by `.agents/skills/`)

- `pdf-handling` — markdown to PDF, used for cover-letter output
- `humanizer` — editing pass over cover-letter prose
- the `tavily` CLI — company research for cover letters; optional, since the skills fall back without it

## Usage

Requires the tools listed under [Dependencies](#dependencies). Run from the repo root, since the CLI reads `data.yaml`, `resume.view.yaml`, and `site.view.yaml` from the current directory.

```sh
mkdir -p dist/resume dist/site
uv run render            # render both (resume + site)
uv run render -m r       # resume only
uv run render -m s       # site only
uv run render -r <path>  # use a different resume view file
```

Or use the convenience scripts: `scripts/render_resume.sh` (render + PDF) and `scripts/render_site.sh` (render + copy into `site/` + serve).

To see what survived filtering, check the `INFO` log line printed by `uv run render` or inspect the generated file.

## `data.yaml`

The single source of truth for all content. Renderers never read it directly — they read it through a view file — but every field below is available to filter.

| Key | Shape | Consumed by |
| --- | --- | --- |
| `name` | string | resume header |
| `info` | mapping: `email`, `phone`, `website`, `github`, `hugging-face`, `linkedin`, `miscellaneous` (list of strings) | resume header |
| `education` | mapping: `university`, `degree`, `location`, `start`, `end`, `gpa`, `courses` (list of strings) | resume only |
| `experience` | list of mappings: `title`, `company`, `location`, `start`, `end`, `bullets` (list of strings) | resume + site |
| `projects` | list of mappings: `title`, `start`, `end`, `url`, `bullets` | resume (`title`, dates, `bullets`) and site (all fields; `url` is also fetched for its `og:image`) |
| `skills` | mapping of category name → list of strings (currently `languages`, `frameworks`, `tools`) | resume + site |
| `certifications` | list of strings | resume + site |

Details worth knowing before you edit it:

- **The site ignores `name`, `info`, and `education`.** It renders three pages — `/experience/`, `/projects/`, `/skills-certifications/` — from the remaining sections.
- **The site iterates `skills` categories dynamically**, so a new category (`databases:`, say) renders without code changes. The resume renderer hardcodes `languages`, `frameworks`, and `tools`, so those three must exist for a resume build.
- **Hyphenated keys become underscores** in the renderer (`hugging-face` is read as `hugging_face`), so keep the hyphen in `data.yaml`.
- **Every project's `url` is fetched during site rendering** and must be reachable; a missing `og:image` falls back to a placehold.co placeholder.
- **LaTeX escaping is partial.** `&` is escaped in `university`, `company`, and `certifications`, and `%` in bullets — other special characters (`_`, `#`, `$`, `{`, `}`) in those fields can break the PDF build.

## View files

A view file is a **filter, not data**. It names top-level keys from `data.yaml` and, for each, selects or trims what gets rendered. The parser treats strings as *object keys* and integers as *list indices*, so how you select depends on whether the source field is a mapping or a list.

A bare key with a null value keeps that field whole:

```yaml
name:          # keep name unchanged

info:          # keep the whole info block
```

To trim a field, give it an `include` and/or `exclude` list:

```yaml
education:
  include:                       # keep only these sub-fields
    - university
    - degree
    - courses:
        include:
          - 0
          - 1                   # nested filter on the courses list

experience:
  include:
    - 1                          # list entries selected by index
    - 0                          # order here is the output order
    - -1                         # negative indices count from the end

skills:
  include:
    - languages:
        exclude:
          - 9                    # drop an item from languages[] by index
    - frameworks
    - tools
```

Rules the parser actually enforces (see `src/render/parser.py`):

- **`include` ordering wins.** List sections render in the index order you write, not in `data.yaml` order, so you can reorder entries by reordering indices.
- **Negative indices work in `include`** (`-1` is the last entry) and can be mixed with positive ones.
- **`exclude` takes indices for lists and key names for objects.** `exclude` on a *list* only accepts integer indices (use non-negative ones: a negative index is silently ignored); `exclude` on an *object* takes field names. Naming a list item's value in `exclude` does nothing.
- **Don't mix integer indices and string keys in one `include`.** The string-keyed entries survive and the indexed ones are silently dropped, which is rarely what you meant.
- **`include: all`, or omitting `include` entirely, keeps the whole field.**
- **A key that doesn't exist raises `KeyError`**, whether it's a top-level key or a field inside `include`. A top-level value must be null or a mapping; a scalar (e.g. `name: 5`) raises `TypeError`.
- **A resume view must keep every section the LaTeX renderer reads** (`name`, `info`, `education`, `experience`, `projects`, `skills`, `certifications`) or rendering fails. Trim *within* sections instead of dropping them.

`site.view.yaml` and `resume.view.yaml` are independent, so the resume and site can show different subsets.

## CI

`.github/workflows/render.yaml` runs on every push to `main` that touches `data.yaml`, `resume.view.yaml`, `site.view.yaml`, `src/render/renderer.py`, `site/**`, or the workflow itself.

1. **`changes`** — `dorny/paths-filter` decides whether the resume and the site each need rebuilding. They are independent: a change to `latex_renderer.py` rebuilds only the resume, one to `jekyll_renderer.py` or `site/**` rebuilds only the site, and edits to `renderer.py`, `data.yaml`, or the workflow rebuild both.
2. **`render`** — runs `uv run render` in the `ghcr.io/astral-sh/uv` container and uploads the generated `resume.tex` and `dist/site` as artifacts.
3. **`build-resume`** (resume changes only) — compiles `resume.tex` with `pdflatex` inside a TeX Live container.
4. **`build-site`** (site changes only) — sets up Ruby, builds the Jekyll site from the rendered markdown, and uploads the Pages artifact.
5. **`release-resume`** — publishes the PDF as a dated GitHub Release (`v<YYYY.MM.DD>-<sha>`).
6. **`deploy-site`** — deploys the built site to GitHub Pages.

Site rendering needs network access, since the renderer fetches each project's `url` to scrape its `og:image` (falling back to a placehold.co image).
