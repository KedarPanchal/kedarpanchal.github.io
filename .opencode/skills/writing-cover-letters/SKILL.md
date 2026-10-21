---
name: writing-cover-letters
description: Use when asked to write a cover letter for a job posting link. Fetches the job description with webfetch, pulls candidate facts from data.yaml, optionally researches the company with the tavily CLI, writes markdown to cover-letters/<company_name>_<job_position>.md, then generates a matching PDF via the pdf-handling skill.
---

# Writing tailored cover letters

Produce a job-specific cover letter from the repo's `data.yaml`, the posted job
description, and (when available) company research. Output both a markdown file
and a PDF with the same base name in `cover-letters/`.

## Inputs

- **Required:** a link to the job description, plus (optionally) the company
  name and exact job title if they are not obvious from the posting.
- **Read-only source:** `data.yaml` is the single source of truth for the
  candidate's facts. **Never modify `data.yaml`.**

## Workflow

1. **Fetch the job description with `webfetch`.** Call `webfetch` on the exact
   URL the user provided. Capture: company name, job title, location,
   responsibilities, required/preferred qualifications, technologies, and any
   stated values or mission language. If the fetch fails, is behind a login,
   or returns boilerplate, ask the user to paste the description and continue
   with that.

2. **Read `data.yaml`.** Extract only verifiable candidate facts: name, contact
   info, education, experience bullets, projects, skills, and certifications.
   Choose the experience/projects/skills that best match the posting's
   requirements. Do not invent employers, dates, metrics, or skills.

3. **Research the company with the `tavily` skill (best effort).** Run the
   Tavily CLI to learn the company's mission, products, culture, or recent news
   so the letter can reference specifics:

   ```
   mkdir -p .tavily
   tvly search "<company name> mission values recent news" --client-name opencode \
     --max-results 5 --json -o .tavily/cover-letter-<company_slug>.json
   ```

   Read the result with `jq`/`grep` or a limited read — do not dump the whole
   JSON file into context. Prefer facts you can cite from the results; skip
   anything unverifiable.

   **Fallback:** if Tavily is not installed, unauthenticated, rate-limited, out
   of credits, or exits non-zero for any reason, do **not** block or keep
   retrying. Skip company research entirely and write the letter using only
   `data.yaml` plus the job description. Note nothing about the failure in the
   letter itself.

4. **Write the cover letter markdown.** Create `cover-letters/` if it does not
   exist, then save to:

   ```
   cover-letters/<company_name>_<job_position>.md
   ```

   Use a lowercase snake_case slug for both parts (replace spaces/punctuation
   with underscores), e.g. `cover-letters/acme_backend_engineer.md`. Structure:

   - Header with the candidate's name and contact details from `data.yaml`
     (`info.email`, `info.phone`, `info.website`, `info.linkedin`, `info.github`).
   - Date, hiring manager / "Hiring Team", company name, and role title.
   - 3–4 short paragraphs: an opening naming the role and company; one or two
     body paragraphs tying specific `data.yaml` experience/project bullets to
     the posting's requirements; a closing with a call to action.
   - Keep it to one page. Match the posting's terminology without fabricating
     experience. Company research should add one or two concrete, relevant
     details — not generic flattery.

5. **Generate the PDF with the `pdf-handling` skill.** Load and follow the
   `pdf-handling` skill's creation workflow to convert the markdown to PDF.
   The output must use the same base name and folder as the markdown:

   ```
   cover-letters/<company_name>_<job_position>.pdf
   ```

   A reliable pipeline is markdown → HTML → WeasyPrint (the creation path
   recommended by `pdf-handling`); keep print-friendly margins and readable
   body text. Verify the PDF exists and is non-zero length before finishing.

## Rules

- **Never edit `data.yaml`.** If the strongest experience for the role is not
  in `data.yaml`, say so instead of inventing it.
- **Facts only.** Every claim about the candidate must trace to `data.yaml`;
  every claim about the company must trace to the job description or Tavily
  results.
- **Tavily is optional.** Its failure changes sourcing, not the deliverable.
- **Two outputs, one base name:** `cover-letters/<company_name>_<job_position>.md`
  and `cover-letters/<company_name>_<job_position>.pdf`.
- Do not commit generated letters unless the user asks.
