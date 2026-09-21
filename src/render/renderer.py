import yaml
import requests
import urllib.parse

from abc import ABC, abstractmethod
from enum import Enum
from types import SimpleNamespace
from bs4 import BeautifulSoup
from .yaml_parser import YamlParser


class Renderer(ABC):
    @abstractmethod
    def render(self, src: SimpleNamespace) -> None:
        pass


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
            f.write(self._experience(src))
            f.write(self._projects(src))
            f.write(self._skills_certifications(src))
            f.write(r"\end{document}")


class JekyllRenderer(Renderer):
    def __init__(self, dest: str):
        self._dest = dest
        self._order_index = 1

    def _make_preamble(self, title: str, permalink: str) -> str:
        result = f"""---
layout: page
title: {title}
permalink: {permalink}
menu: true
order: {self._order_index}
---
"""
        self._order_index += 1
        return result

    def _experience(self, src: SimpleNamespace, dest: str) -> None:
        result_list = []

        with open(f"{dest}/rendered_experience.md", 'w') as md:
            md.write(self._make_preamble("Work Experience", "/experience/"))
            for i, experience in enumerate(src.experience):
                result_list += [
                    "{% capture experience_" + str(i) + " %}",
                    *[f"- {bullet}" for bullet in experience.bullets],
                    "{% endcapture %}",
                    "{% include experience-listing.html "
                      + f"title='{experience.title}' "
                      + f"company='{experience.company}' "
                      + f"location='{experience.location}' "
                      + f"start='{experience.start}' "
                      + f"end='{experience.end}' "
                      + f"bullets=experience_{i} "
                      + " %}"
                ]
            md.write('\n'.join(result_list))

    def _get_opengraph_url(self, url: str) -> str:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        og_tag = soup.find("meta", property="og:image")
        if og_tag and og_tag.get("content"):
            return og_tag["content"]
        placehold_params = {"text": url}
        return f"https://placehold.co/400x400?{urllib.parse.urlencode(placehold_params)}"

    def _projects(self, src: SimpleNamespace, dest: str) -> None:
        result_list = []
        columns = ["left_column", "right_column"]
        column_index = 0

        with open(f"{dest}/rendered_projects.md", 'w') as md:
            md.write(self._make_preamble("Projects", "/projects/"))

            for project in src.projects:
                text_column = f"{columns[column_index % 2]}_{column_index}"
                image_column = f"{columns[(column_index + 1) % 2]}_{column_index}"
                result_list = [
                    f"### [{project.title}]({project.url})",
                    "{% capture " + text_column + " %}",
                    f"*{project.start} - {project.end}*",
                    *[f"- {bullet}" for bullet in project.bullets],
                    "{% endcapture %}"
                    "{% capture " + image_column + " %}",
                    f"![{project.title}]({self._get_opengraph_url(project.url)})",
                    "{% endcapture %}",
                    "{% include two-column.html col1=" + f"left_column_{column_index}" + " col2=" + f"right_column_{column_index}" + " %}",
                    "<hr />"
                ]
                md.write('\n'.join(result_list) + '\n\n')
                column_index += 1

    def _skills_certifications(self, src: SimpleNamespace, dest: str) -> None:
        result_list = []

        with open(f"{dest}/rendered_skills_certifications.md", 'w') as md:
            md.write(self._make_preamble("Skills & Certifications", "/skills-certifications/"))
            for category, items in src.skills.__dict__.items():
                result_list += [
                    "{% capture " + category + "_list %}",
                    *[f"- {item}" for item in items],
                    "{% endcapture %}",
                    "{% include dropdown-list.html " 
                      + f"title='{category.title()}' " 
                      + f"content={category}_list "
                      + f"short=true"
                      + " %}"
                ]
            result_list += [
                "{% capture certifications_list %}",
                *[f"- {certification}" for certification in src.certifications],
                "{% endcapture %}",
                "{% include dropdown-list.html title='Certifications' content=certifications_list %}"
            ]
            md.write('\n'.join(result_list) + '\n\n')

    def render(self, src: SimpleNamespace) -> None:
        self._experience(src, self._dest)
        self._projects(src, self._dest)
        self._skills_certifications(src, self._dest)
