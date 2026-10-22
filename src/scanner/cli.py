"""Run the scanner from the command line."""

import argparse
import yaml 

from .convert import pdf_to_images
from .align import align, AlignmentError
from .extract import extract
from .validate import validate
from .export import export

def run(pdf, lesson="", school="", class_name="", out_dir=None):
    """
    Reads every page of PDF and writes results to CSV
        pdf:            PDF file path
        config_path:    config file path 
        school:         school name 
        class_name:     class name 
        lesson_id:      lesson id (to match with a lessons.json)
        out_dir:        output folder 
    """
    config = load_config("config/config.yaml")
    data = []

    for name, image in pdf_to_images(pdf, dpi=config["convert"]["dpi"]):
        # straighten page
        try:
            sheet = align(image, config, page=name)

        except AlignmentError as e:
            data.append({"path": name, "error": True})
            continue

        # measure bubbles, then decide answers
        scores = extract(sheet, config)
        data.append(validate(scores, config, name))

    # tag every page, including pages that failed alignment
    for d in data:
        d["school"] = school
        d["class"] = class_name
        d["lesson_id"] = lesson

    export(data, config, out_dir)

    # summary
    errors = sum(d["error"] for d in data)
    print(f"{len(data)} pages: {len(data) - errors} ok, {errors} need review")

def load_config(path):
    """
    Reads the YAML config file and returns as dict 
        path:       config file path 
    """
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config["regions"] = {k: tuple(v) for k, v in config["regions"].items()}
    return config

def main():
    """
    Args & Startup 
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="path to PDF")
    parser.add_argument("-s", "--school", default="", help="school name")
    parser.add_argument("-c", "--class", dest="class_name", default="", help="class name")
    parser.add_argument("-o", "--output", default=None, help="folder to write the CSV to")
    parser.add_argument("-l", "--lesson", default=None, help="lesson id (school + year + L + lesson_num)")
    args = parser.parse_args()

    run(args.f, school=args.school, class_name=args.class_name, lesson=args.lesson, out_dir=args.output)


if __name__ == "__main__":
    main()