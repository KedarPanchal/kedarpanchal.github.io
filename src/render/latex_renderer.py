from .renderer import Renderer

from types import SimpleNamespace


# LaTeX special characters and their text-mode replacements. A string is escaped
# in a single pass so replacements are never escaped again.
_LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(value: object) -> str:
    return "".join(_LATEX_SPECIAL_CHARS.get(char, char) for char in str(value))


class LatexRenderer(Renderer):
    def __init__(self, dest: str):
        self._dest = dest

    def _preamble(self) -> str:
        return r"""
\documentclass[9pt]{article}
\pagestyle{empty}

\usepackage[hidelinks]{hyperref}
\usepackage[none]{hyphenat}
\raggedright
\usepackage[margin=0.45in]{geometry}
\usepackage[sfdefault]{carlito}
\usepackage{setspace}
\setstretch{0.92}
\usepackage{scalefnt}
\usepackage{enumitem}
\setlist[itemize]{noitemsep}

\newcommand{\resumesection}[1]{\noindent\underline{\makebox[\textwidth][l]{\scalefont{1.1}\textbf{#1}}}}

\begin{document}
"""
    
    def _info(self, src: SimpleNamespace) -> str:
        email = escape_latex(src.info.email)
        website = escape_latex(src.info.website)
        linkedin = escape_latex(src.info.linkedin)
        github = escape_latex(src.info.github)
        hugging_face = escape_latex(src.info.hugging_face)

        result_list = [
            r"\begin{center}",
            r"{\Huge \textbf{" + escape_latex(src.name) + r"}} \\ [0.5em]",
            r"\small \href{mailto:" + email + r"}{" + email + r"} {\textbar }",
            r"\small " + escape_latex(src.info.phone) + r" {\textbar }",
            r"\small Website: \href{https://" + website + r"}{" + website + r"} {\textbar }",
            r"\small LinkedIn: \href{https://www.linkedin.com/in/" + linkedin + r"}{" + linkedin + r"} \\",
            r"\small GitHub: \href{https://www.github.com/" + github + r"}{" + github + r"} {\textbar }",
            r"\small Hugging Face: \href{https://www.huggingface.co/" + hugging_face + r"}{" + hugging_face + r"}",
        ]
        # Add miscellaneous information if it exists
        for i, miscellany in enumerate(src.info.miscellaneous):
            # Prefix with a text bar to separate the first item from Hugging Face
            if i == 0:
                to_append = r"{\textbar } \small " + escape_latex(miscellany)
            else:
                to_append = r"\small " + escape_latex(miscellany)
            # Only add the separator if it's not the last item in the list
            if i < len(src.info.miscellaneous) - 1:
                to_append += r" {\textbar }"
            result_list.append(to_append)

        result_list.append(r"\end{center}")
        return '\n'.join(result_list)

    def _education(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{EDUCATION}",
            r"\textbf{" + escape_latex(src.education.university) + r"} \hfill " + escape_latex(src.education.location) + r"\\",
            r"\textit{" + escape_latex(src.education.degree) + r"} \hfill \textit{" + f"{escape_latex(src.education.start)} - {escape_latex(src.education.end)}" + r"}",
            r"\begin{itemize}",
            r"\item \textbf{GPA:} " + escape_latex(src.education.gpa),
            r"\item \textbf{Relevant Coursework:} " + ', '.join(escape_latex(course) for course in src.education.courses),
            r"\end{itemize}",
        ]
        return '\n'.join(result_list)

    def _experience(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{WORK EXPERIENCE}",
        ]
        for experience in src.experience:
            result_list += [
                r"\noindent\textbf{" + escape_latex(experience.company) + r"} \hfill " + escape_latex(experience.location) + r"\\",
                r"\textit{" + escape_latex(experience.title) + r"} \hfill \textit{" + f"{escape_latex(experience.start)} - {escape_latex(experience.end)}" + r"}",
                r"\begin{itemize}",
                *[r"\item " + escape_latex(bullet) for bullet in experience.bullets],
                r"\end{itemize}",
            ]
        return '\n'.join(result_list)

    def _projects(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{PROJECTS}",
        ]
        for project in src.projects:
            result_list += [
                r"\noindent\textbf{" + escape_latex(project.title) + r"} \hfill \textit{" + f"{escape_latex(project.start)} - {escape_latex(project.end)}" + r"}",
                r"\begin{itemize}",
                *[r"\item " + escape_latex(bullet) for bullet in project.bullets],
                r"\end{itemize}",
            ]
        return '\n'.join(result_list)
    
    def _skills_certifications(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{SKILLS \& CERTIFICATIONS}",
            r"\begin{itemize}",
            r"\item \textbf{Programming Languages:} " + ', '.join(escape_latex(language) for language in src.skills.languages),
            r"\item \textbf{Frameworks:} " + ', '.join(escape_latex(framework) for framework in src.skills.frameworks),
            r"\item \textbf{Tools:} " + ', '.join(escape_latex(tool) for tool in src.skills.tools),
            r"\item \textbf{Certifications:} " + ', '.join(escape_latex(certification) for certification in src.certifications),
            r"\end{itemize}"
        ]
        return '\n'.join(result_list)

    def render(self, src: SimpleNamespace) -> None:
        with open(self._dest, 'w') as f:
            f.write(self._preamble())
            f.write(self._info(src))
            f.write(self._education(src))
            f.write(self._experience(src))
            f.write(self._projects(src))
            f.write(self._skills_certifications(src))
            f.write(r"\end{document}")
