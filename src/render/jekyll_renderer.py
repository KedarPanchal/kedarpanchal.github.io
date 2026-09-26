from .renderer import Renderer

from types import SimpleNamespace
import requests
import urllib.parse
from bs4 import BeautifulSoup


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
