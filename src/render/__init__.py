from . import parser
from .latex_renderer import LatexRenderer
from .jekyll_renderer import JekyllRenderer

import logging
import argparse

logger = logging.getLogger(__name__)

arg_parser = argparse.ArgumentParser(description="Render resume and Jekyll site from YAML data.")
arg_parser.add_argument("--resume-view", "-r", type=str, default="resume.view.yaml", help="Path to the resume view YAML file.")
arg_parser.add_argument("--mode", "-m", type=str, choices=['r', 's', "rs", "sr"], default="rs", help="Mode of operation: 'r' for resume only, 's' for site only, 'rs' or 'sr' for both.")
args = arg_parser.parse_args()

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    p = parser.YAMLParser("data.yaml")
    
    if 'r' in args.mode:
        logger.info("Starting resume rendering process...")
        resume_data = p.parse_view(args.resume_view)

        logger.info(resume_data)
        latex_renderer = LatexRenderer("dist/resume/resume.tex")

        resume_namespace = resume_data.to_namespace()
        if not isinstance(resume_namespace, parser.SimpleNamespace):
            logger.error("Parsed resume data is not a SimpleNamespace. Cannot render resume.")
            return

        latex_renderer.render(resume_namespace)
        logger.info("Resume rendering process completed successfully.")
    else:
        logger.info("Skipping resume rendering process.")

    if 's' in args.mode:
        logger.info("Starting Jekyll site render process...")
        jekyll_data = p.parse_view("site.view.yaml")

        logger.info(jekyll_data)
        jekyll_renderer = JekyllRenderer("dist/site")
        
        jekyll_namespace = jekyll_data.to_namespace()
        if not isinstance(jekyll_namespace, parser.SimpleNamespace):
            logger.error("Parsed Jekyll site data is not a SimpleNamespace. Cannot render site.")
            return

        jekyll_renderer.render(jekyll_namespace)
        logger.info("Jekyll site render process completed successfully.")
    else:
        logger.info("Skipping Jekyll site rendering process")
