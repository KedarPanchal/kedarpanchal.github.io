---
name: writing-cover-letters
description: Use when writing a cover letter for a job posting. Fetches the posting, draws candidate facts from data.yaml, optionally researches the company with the tavily CLI, writes cover-letters/<company>_<role>.md, humanizes it, and produces a matching PDF.
---

# Writing tailored cover letters

Produce a job-specific cover letter from three sources: the repo's `data.yaml`,
the posted job description, and, when available, company research. Deliver a
markdown file, a PDF with the same base name, and a Google Drive upload.

## When to use

- The user gives a job posting and asks for a cover letter, or asks for one
  alongside a tailored resume.
- The user asks to rewrite or tighten an existing letter in `cover-letters/`.

Do not use this skill to tailor a resume; use `writing-resume-views` for that.
The two are often requested together, and they are independent: this skill
never touches view files, and that one never writes letters.

## Inputs

- The job posting: a URL, or text the user pasted.
- Optionally, the company name, role title, and hiring manager's name, if they
  are not obvious from the posting.

## Outputs

- `cover-letters/<company>_<role>.md` — the letter source.
- `cover-letters/<company>_<role>.pdf` — the same letter as a PDF.
- The PDF uploaded to the Drive folder configured for cover letters, with its
  link copied to the clipboard.

Use a lowercase snake_case slug for the company and the role, for example
`cover-letters/acme_backend_engineer.md` and
`cover-letters/acme_backend_engineer.pdf`.

## Workflow

1. **Fetch the posting.** Call your URL-reading tool on the exact URL the user
   provided (`webfetch`; `read_url` where that is the tool exposed). Capture
   the company name, job title, location, responsibilities, required and
   preferred qualifications, technologies, and any stated values or mission
   language. If the fetch fails, is behind a login, or returns boilerplate,
   ask the user to paste the description and continue with that.

2. **Read `data.yaml`.** It is the single source of truth for the candidate's
   facts. Read it fresh on every run; do not modify it. Pull the name, contact
   details, education, experience bullets, projects, skills, and
   certifications. Choose the experience, projects, and skills that best match
   the posting. Do not invent employers, dates, metrics, or skills.

3. **Research the company, best effort.** When the `tavily` CLI is available,
   look up the company's mission, products, culture, or recent news so the
   letter can cite specifics:

   ```sh
   mkdir -p .tavily
   tvly search "<company> mission values recent news" --client-name opencode \
     --max-results 5 --json -o .tavily/cover-letter-<company_slug>.json
   ```

   Read the result with `jq` or a narrow read; do not dump the whole JSON file
   into context. Keep only facts you can cite from the results.

   If Tavily is not installed, unauthenticated, rate-limited, out of credits,
   or exits non-zero, do not retry and do not stall. Skip company research and
   write from `data.yaml` plus the posting. Never mention the failure in the
   letter.

4. **Write the markdown.** Create `cover-letters/` if needed and save under the
   output name above. See [Reference: letter format](#reference-letter-format)
   for the structure. Keep it to one page.

5. **Humanize and revise.** If the `humanizer` skill is available, load it and
   apply it to the draft. Otherwise make the same edits directly: remove
   generic phrases, stock transitions, and buzzwords; vary sentence length;
   cut inflated or vague claims; drop false modesty. The tone should be
   direct, specific, and personable, with the candidate's strengths tied to
   what the company needs.

6. **Generate the PDF.** Load the `pdf-handling` skill and follow its creation
   workflow, converting the same markdown into the PDF output name above. A
   reliable path is markdown to HTML and then WeasyPrint, with print-friendly
   margins and readable body text. If WeasyPrint is unavailable, render the
   HTML with headless Chrome (`--headless --print-to-pdf`) instead. The PDF
   must match the markdown's folder and base name.

7. **Upload the PDF.** Use the `google-docs` skill's `drive_manager.rb`:

   ```sh
   ruby <google-docs-skill>/scripts/drive_manager.rb upload \
     --file cover-letters/acme_backend_engineer.pdf \
     --folder-id <cover_letter_folder_id>
   ```

   Resolve `<google-docs-skill>` against that skill's base directory (for
   example `~/.agents/skills/google-docs`), not this repo. Read
   `<cover_letter_folder_id>` from the `cover_letter_folder_id` key in
   `configs/gsuite.jsonc`. That file is local: if it does not exist, copy
   `configs/gsuite.example.jsonc` and ask the user for the folder ID. Never
   invent an ID. The command prints JSON; copy the link with
   `... | jq -r '.file.web_view_link' | pbcopy`, or print it when `pbcopy` is
   unavailable. If the config or credentials are missing, skip the upload and
   tell the user where the local PDF is.

## Reference: letter format

The header and sign-off come from `data.yaml`; the middle addresses the
posting.

- **Header:** `<name>`, then `info.email`, `info.phone`, `info.website`,
  `info.linkedin`, and `info.github`, separated by pipes or on one line.
- **Date:** the current date.
- **Recipient:** the hiring manager's name when known, otherwise
  `Hiring Team`, then the company name and location.
- **Salutation:** `Dear <name>,` or `Dear Hiring Team,`.
- **Body:** three to four short paragraphs.
  - Opening: name the role and company, and state the single strongest reason
    the candidate fits.
  - Body: one or two paragraphs tying specific `data.yaml` experience or
    project bullets to the posting's requirements. Use one or two concrete
    company details from research if you have them.
  - Closing: restate fit in one sentence and ask for the next step.
- **Sign-off:** a short closing and the candidate's name.

Keep the language concrete. Match the posting's terminology without keyword
stuffing, and avoid generic flattery that would fit any employer.

## Rules

- **Never edit `data.yaml`.** If the strongest experience for the role is not
  in it, say so instead of inventing it.
- **Facts only.** Every claim about the candidate traces to `data.yaml`; every
  claim about the company traces to the posting or Tavily results.
- **Tavily is optional.** Its failure changes sourcing, not the deliverable.
- **One page, one base name.** The markdown and PDF share the folder and base
  name and both must exist before finishing.
- **No placeholders in the final letter.** Replace every `<...>` before
  generating the PDF.
- **Do not commit generated letters** unless the user asks.

## Verify

1. Confirm both files exist under the expected base name and that the PDF is
   non-zero length.
2. Check the PDF is one page, for example
   `pdfinfo cover-letters/<base>.pdf | grep Pages`.
3. Read the PDF text back (`pdftotext cover-letters/<base>.pdf -`) and check
   for leftover placeholders, repeated sentences, and broken contact details.
4. Cross-check the letter against the posting: the role and company are named
   correctly, the body addresses the stated requirements, and every candidate
   claim traces to `data.yaml`.
5. Confirm the upload link was copied or printed when the upload ran.
