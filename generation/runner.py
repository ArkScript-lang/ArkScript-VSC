import re
import os
import argparse
import json

def read_file_in_same_dir(file: str) -> dict:
    content = None
    with open(os.path.join(os.path.dirname(__file__), file), "r", encoding="utf-8") as f:
        content = json.loads(f.read())
    return content

def fetch_std_functions(path) -> dict:
    p = r"^\(let +([a-zA-Z:_]+) +.*$"
    keywords = {}

    for file_path in [f for f in os.listdir(path) if f.endswith('.ark')]:
        with open(os.path.join(path, file_path), "r", encoding="utf-8") as file:
            name = file_path.split('.')[0].lower()
            keywords[name] = []

            for line in file.readlines():
                if re.match(p, line):
                    keywords[name].append(re.split(p, line)[1])

    return keywords

def generate_from_stems(out_path: str, std_keywords: dict):
    content: dict = read_file_in_same_dir("language.structure.json")
    builtins: dict = read_file_in_same_dir("builtins.json")

    # getting the functions by merging the builtins json and the std keywords
    funcs = {}
    bnames: list = list(builtins['functions'].keys())
    snames: list = list(std_keywords.keys())
    to_remove = []
    for n in bnames:
        if n in snames:
            funcs[n] = [*builtins['functions'][n], *std_keywords[n]]
            to_remove.append(n)
        else:
            funcs[n] = builtins['functions'][n]
    
    snames = [e for e in snames if e not in to_remove]
    for n in snames:
        funcs[n] = std_keywords[n]

    # making sure there are no empty rules
    funcs = {key: funcs[key] for key in funcs if funcs[key]}

    # inserting the functions in the language file
    for fun in funcs:
        content['repository']['builtins']['patterns'].append({
            "name": f"entity.name.function.{fun}.arkscript",
            "match": f"\\b({'|'.join(funcs[fun])}) "
        })

    # adding the arkdoc @params to the content
    content['repository']['comments']['patterns'].insert(0, {
            "name": "storage.type.class.arkdoc.arkscript",
            "match": f" *({'|'.join([f'@{e}' for e in builtins['arkdoc']])})"
	})

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(json.dumps(content, indent=4))


def main(std, language):
    r = fetch_std_functions(std)
    generate_from_stems(language, r)
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("std_path")
    parser.add_argument("-L", "--langfile", default="./syntaxes/arkscript.tmLanguage.json")

    args = parser.parse_args()

    main(args.std_path, args.langfile)
