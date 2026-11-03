---
name: writing-resume-views
description: Use when tailoring the resume to a job posting by writing a view YAML file in tailored-resumes/ and rendering it with `uv run render -m r -r <view>`. Covers fetching the posting, mapping it onto data.yaml indices, the include/exclude filter DSL, the PDF build, and the Drive upload.
---

# Writing resume view files

A view file is a **filter, not data**. It names top-level keys from `data.yaml`
and selects or trims what the resume renderer prints. Tailoring a resume means
writing a new view file; it never means editing `data.yaml`.

## When to use

- The user asks for a resume tailored to a specific job posting, company, or
  role.
- The user wants an existing tailored resume rebuilt or trimmed.
- The user asks which `data.yaml` entries to show for a role.

Do not use this skill to change resume wording or add content. A view can
select, trim, and reorder, but it cannot rewrite text. If the posting needs
phrasing that `data.yaml` does not have, tell the user instead of editing the
source.

## Inputs

- The job posting: a URL, or text the user pasted.
- Optionally, the exact company and role title, if the posting does not make
  them obvious.

## Outputs

- `tailored-resumes/<company>_<role>.view.yaml` — the filter.
- `tailored-resumes/<company>_<role>.pdf` — the rendered resume.
- The PDF uploaded to the Google Drive folder configured for resumes, with its
  link copied to the clipboard.

Use a lowercase snake_case slug for the company and the role, for example
`tailored-resumes/acme_backend_engineer.view.yaml` and
`tailored-resumes/acme_backend_engineer.pdf`.

## Workflow

1. **Fetch the posting.** If the user gave a URL, fetch it with your
   URL-reading tool (`webfetch`; `read_url` where that is the tool exposed).
   If the user pasted the description, use it as-is. If the fetch fails, is
   behind a login wall, or returns boilerplate, ask the user to paste the text
   rather than guessing.

2. **Extract the requirements.** Record the role title, company, location,
   responsibilities, required and preferred qualifications, technologies, and
   any repeated keywords. Keep these notes for the mapping step and for the
   final review.

3. **Read `data.yaml`.** It is the single source of truth for all content.
   Read it fresh every time: indices are positions, so any edit shifts them.
   Do not add, remove, or reword anything in it.

4. **Map requirements to entries.** Pick the `experience`, `projects`,
   `skills`, and `certifications` entries that best match the posting. Note
   their list indices, because list sections are selected by index, not by
   name. Prefer the strongest evidence for the role over a literal keyword
   match; keep enough entries that the resume still reads as a career, not a
   keyword list.

5. **Create the view file.** Start from `resume.view.yaml`, save it under the
   output name above, and adjust the `include`/`exclude` lists. Keep every
   top-level section (see [Reference: `data.yaml` shape](#reference-datayaml-shape));
   trim within sections instead of dropping them.

6. **Render the resume.**

   ```sh
   mkdir -p dist/resume
   uv run render -m r -r tailored-resumes/acme_backend_engineer.view.yaml
   ```

   This writes `dist/resume/resume.tex`. Do not use
   `scripts/render_resume.sh` for a tailored view: that script hardcodes the
   default `resume.view.yaml` and accepts no `-r` argument.

7. **Compile the PDF.**

   ```sh
   cd dist/resume && pdflatex -interaction=nonstopmode resume.tex
   ```

   Check the exit status and the `Output written on resume.pdf (...)` line.
   Then move the result next to its view file:

   ```sh
   mv dist/resume/resume.pdf tailored-resumes/acme_backend_engineer.pdf
   ```

8. **Upload the PDF.** Use the `google-docs` skill's `drive_manager.rb`:

   ```sh
   ruby <google-docs-skill>/scripts/drive_manager.rb upload \
     --file tailored-resumes/acme_backend_engineer.pdf \
     --folder-id <resume_folder_id>
   ```

   Resolve `<google-docs-skill>` against that skill's base directory (for
   example `~/.agents/skills/google-docs`), not this repo. Read
   `<resume_folder_id>` from the `resume_folder_id` key in
   `configs/gsuite.jsonc`. That file is local: if it does not exist, copy
   `configs/gsuite.example.jsonc` and ask the user for the folder ID. Never
   invent an ID. The command prints JSON; copy the link with
   `... | jq -r '.file.web_view_link' | pbcopy`, or print it when `pbcopy` is
   unavailable. If the config or credentials are missing, skip the upload and
   tell the user where the local PDF is.

## Reference: `data.yaml` shape

The LaTeX renderer reads every field below unconditionally, so a resume view
must keep all of them. Dropping a top-level key or a field inside one raises
`AttributeError` during rendering.

| Key | Shape | Fields |
| --- | --- | --- |
| `name` | string | — |
| `info` | mapping | `email`, `phone`, `website`, `github`, `hugging-face`, `linkedin`, `miscellaneous` (list of strings) |
| `education` | mapping | `university`, `degree`, `location`, `start`, `end`, `gpa`, `courses` (list of strings) |
| `experience` | list of mappings | `title`, `company`, `location`, `start`, `end`, `bullets` (list of strings) |
| `projects` | list of mappings | `title`, `start`, `end`, `url`, `bullets` (list) |
| `skills` | mapping | `languages`, `frameworks`, `tools` (each a list of strings) |
| `certifications` | list of strings | — |

Notes:

- `projects.url` is not printed on the resume; the site renderer uses it.
- `skills` is hardcoded to `languages`, `frameworks`, and `tools` by the
  renderer. A new category renders on the site but not on the resume.
- Hyphenated keys become underscores in the renderer (`hugging-face` is read
  as `hugging_face`), so keep the hyphen in `data.yaml`.
- LaTeX special characters are escaped for you, so `&`, `%`, `_`, and similar
  are safe in the data.

## Reference: filter syntax

Each top-level key maps to either nothing (keep the field whole) or an object
with `include` and/or `exclude`. The excerpt below is syntax, not a complete
view; a real view must keep every top-level section.

```yaml
# Keep a field unchanged: a bare key with a null value.
name:

# Trim a mapping by sub-key name, with a nested filter on a list of strings.
education:
  include:
    - university
    - degree
    - courses:
        include: [0, 1, 2, 3]

# Select list entries by index; the order here is the output order.
experience:
  include: [1, 2]

projects:
  include: [1, 0]

# Keep a mapping's sub-keys and drop one item from a list inside it.
skills:
  include:
    - languages:
        exclude: [8]      # languages[8], by position
    - frameworks
    - tools

# Pick list entries; -1 counts from the end.
certifications:
  include: [0, 2, -1]
```

## Reference: filter rules

These describe what `src/render/parser.py` actually does.

- **A key with a null value keeps the whole field.** Omitting `include` does
  the same, and `include: all` is equivalent.
- **Strings select mapping keys; integers select a 0-based child position.**
  On a list, position is the list index. On a mapping, position is the field
  order in `data.yaml`, which is fragile: use key names for mappings.
- **`include` order is output order.** For list sections the rendered order
  follows the indices you write, not the order in `data.yaml`, so reorder
  entries by reordering indices.
- **Negative indices in `include` count from the end.** `-1` is the last
  entry, `-2` the penultimate, and they can be mixed with positive indices.
  They break when `data.yaml` changes, so recheck them before finishing.
- **Do not mix strings and integers in one `include` on a list.** A string is
  looked up as a key on a list, finds nothing, and raises
  `KeyError: "<name> is an invalid key"`. Pick one kind per field.
- **`exclude` takes key names for mappings and non-negative indices for
  lists.** Naming a list item's *value* (for example `- Haskell`) matches no
  key and is silently ignored. A negative index in `exclude` is silently
  ignored too.
- **There is no `exclude: all`.** The string is treated as a key name and
  ignored; it does not drop the field.
- **`include` and `exclude` can be combined on one key.** `include` copies the
  selection, then `exclude` prunes it.
- **`exclude` works without `include`.** The whole field is copied first and
  then pruned, e.g. `experience: { exclude: [0] }`.
- **Nested filters are one-key mappings inside `include`**, as in
  `- courses: { include: [...] }`. They only work through mapping keys: a list
  element cannot be nested into, so you cannot select individual experience or
  project bullets. Per-project bullets are all or nothing.
- **A missing key raises `KeyError`**, whether it is a top-level key or a key
  inside `include` or a nested filter.
- **A top-level value must be null or a mapping.** A scalar such as `name: 5`
  raises `TypeError`.

## Rules

- **Never edit `data.yaml`.** If the best evidence for the role is missing
  from it, say so; do not invent or reword content.
- **Keep every top-level section** listed in the shape table. Resume views trim
  within sections; they cannot drop one.
- **Always re-read `data.yaml` before writing indices.** They are positions,
  so they go stale as soon as the data changes.
- **Tailor across every section**, not just `skills`. The posting's keywords
  should influence which experience and projects appear and in what order.
- **Leave out what does not help.** An unrelated entry costs space and
  attention; the resume should stay one page.
- **Do not mirror the posting so literally** that you drop relevant context or
  the most recent role.

## Verify

1. Run `uv run render -m r -r tailored-resumes/<view>` and check the exit
   status. The `INFO` log prints the filtered tree, so read it to confirm what
   survived.
2. Inspect `dist/resume/resume.tex` for the entries you meant to include, in
   the order you meant, and for no missing sections.
3. Compile with `pdflatex` and confirm the output is one page. If it spills
   over, trim entries rather than shrinking content.
4. Compare the result against the extracted requirements: the strongest
   matching experience and projects should be present, and the included skills
   and certifications should cover the technologies the posting names.
5. Confirm the view file and PDF exist under the expected base name, and that
   the upload link was copied or printed when the upload ran.
