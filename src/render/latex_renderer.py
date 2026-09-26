from .renderer import Renderer

from types import SimpleNamespace


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

\newcommand{\resumesection}[1]{\noindent\underline{\makebox[\textwidth][l]{\scalefont{1.1}\textbf{#1}}}}

\begin{document}
"""
    
    def _info(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\begin{center}",
            r"{\Huge \textbf{" + src.name + r"}} \\ [0.5em]",
            r"\small \href{mailto:" + src.info.email + r"}{" + src.info.email + r"} {\textbar }",
            r"\small " + src.info.phone + r" {\textbar }",
            r"\small Website: \href{https://" + src.info.website + r"}{" + src.info.website + r"} {\textbar }",
            r"\small LinkedIn: \href{https://www.linkedin.com/in/" + src.info.linkedin + r"}{" + src.info.linkedin + r"} \\",
            r"\small GitHub: \href{https://www.github.com/" + src.info.github + r"}{" + src.info.github + r"} {\textbar }",
            r"\small Hugging Face: \href{https://www.huggingface.co/" + src.info.hugging_face + r"}{" + src.info.hugging_face + r"}",
        ]
        # Add miscellaneous information if it exists
        for i, miscellany in enumerate(src.info.miscellaneous):
            # Prefix with a text bar to separate the first item from Hugging Face
            if i == 0:
                to_append = r"{\textbar } \small " + miscellany
            else:
                to_append = r"\small " + miscellany
            # Only add the separator if it's not the last item in the list
            if i < len(src.info.miscellaneous) - 1:
                to_append += r" {\textbar }"
            result_list.append(to_append)

        result_list.append(r"\end{center}")
        return '\n'.join(result_list)

    def _education(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{EDUCATION}",
            r"\textbf{" + src.education.university.replace('&', r"\&") + r"} \hfill " + src.education.location + r"\\",
            r"\textit{" + src.education.degree + r"} \hfill \textit{" + f"{src.education.start} - {src.education.end}" + r"}",
            r"\begin{itemize}",
            r"\item \textbf{GPA:} " + str(src.education.gpa),
            r"\item \textbf{Relevant Coursework:} " + ', '.join(src.education.courses),
            r"\end{itemize}",
        ]
        return '\n'.join(result_list)

    def _experience(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{WORK EXPERIENCE}",
        ]
        for experience in src.experience:
            result_list += [
                r"\noindent\textbf{" + experience.company.replace('&', r"\&") + r"} \hfill " + experience.location + r"\\",
                r"\textit{" + experience.title + r"} \hfill \textit{" + f"{experience.start} - {experience.end}" + r"}",
                r"\begin{itemize}",
                *[r"\item " + bullet.replace('%', r"\%") for bullet in experience.bullets],
                r"\end{itemize}",
            ]
        return '\n'.join(result_list)

    def _projects(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{PROJECTS}",
        ]
        for project in src.projects:
            result_list += [
                r"\noindent\textbf{" + project.title + r"} \hfill \textit{" + f"{project.start} - {project.end}" + r"}",
                r"\begin{itemize}",
                *[r"\item " + bullet.replace('%', r"\%") for bullet in project.bullets],
                r"\end{itemize}",
            ]
        return '\n'.join(result_list)
    
    def _skills_certifications(self, src: SimpleNamespace) -> str:
        result_list = [
            r"\resumesection{SKILLS \& CERFIFICATIONS}",
            r"\begin{itemize}",
            r"\item \textbf{Programming Languages:} " + ', '.join(src.skills.languages),
            r"\item \textbf{Frameworks:} " + ', '.join(src.skills.frameworks),
            r"\item \textbf{Tools:} " + ', '.join(src.skills.tools),
            r"\item \textbf{Certifications:} " + ', '.join(map(lambda c: c.replace('&', r"\&"), src.certifications)),
            r"\end{itemize}"
        ]
        return '\n'.join(result_list)

    def render(self, src: SimpleNamespace) -> None:
        with open(self._dest, 'w') as f:
            f.write(self._preamble())
            f.write(self._info(src))
            f.write(self._education(src))
            f.write(self._skills_certifications(src))
            f.write(self._experience(src))
            f.write(self._projects(src))
            f.write(r"\end{document}")



