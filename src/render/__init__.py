from . import yaml_parser
from . import renderer

import logging
import argparse

logger = logging.getLogger(__name__)

arg_parser = argparse.ArgumentParser(description="Render resume and Jekyll site from YAML data.")
arg_parser.add_argument("--resume-view", "-r", type=str, default="resume.view.yaml", help="Path to the resume view YAML file.")
arg_parser.add_argument("--mode", "-m", type=str, choices=['r', 's', "rs", "sr"], default="rs", help="Mode of operation: 'r' for resume only, 's' for site only, 'rs' or 'sr' for both.")
args = arg_parser.parse_args()

def main() -> None:

    logging.basicConfig(level=logging.INFO)
    parser = yaml_parser.YamlParser("data.yaml")
    
    if 'r' in args.mode:
        logger.info("Starting resume rendering process...")
        resume_data = parser.load(args.resume_view)
        logger.info(resume_data)
        latex_renderer = renderer.LatexRenderer("dist/resume/resume.tex")
        latex_renderer.render(resume_data)
        logger.info("Resume rendering process completed successfully.")
    else:
        logger.info("Skipping resume rendering process.")

    if 's' in args.mode:
        logger.info("Starting Jekyll site render process...")
        jekyll_data = parser.load("site.view.yaml")
        logger.info(jekyll_data)
        jekyll_renderer = renderer.JekyllRenderer("dist/site")
        jekyll_renderer.render(jekyll_data)
        logger.info("Jekyll site render process completed successfully.")
    else:
        logger.info("Skipping Jekyll site rendering process")
