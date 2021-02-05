import yaml
import os

strings = dict()


def refresh() -> iter:
    for file in os.listdir("res/lang"):
        yield "./res/lang/" + file


def load(filename: str):
    global strings
    text: str
    with open(filename, encoding='utf-8') as file:
        text = file.read()
        # print(text)
    strings = yaml.safe_load(text)


def get_name(filename: str):
    text: str
    with open(filename, encoding='utf-8') as file:
        text = file.read()
        # print(text)
    try:
        lang = yaml.safe_load(text)
    except yaml.YAMLError as err:
        raise ValueError("Error parsing YAML file.") from err
    if type(lang) is not dict:
        raise ValueError("Invalid YAML language file.")
    if "lang_name" not in lang:
        raise KeyError("lang_name")
    return lang["lang_name"]


def get_str(string: str, report=False) -> str:
    global strings
    # print(strings)
    keys = string.split('.')
    fetch = strings
    for k in keys:
        if k not in fetch:
            if report:
                raise KeyError(str)
            else:
                return string
        else:
            fetch = fetch[k]
    if type(fetch) is not str:
        if report:
            raise KeyError(str)
        else:
            return string
    return fetch


if __name__ == '__main__':
    load("res/lang/pt-br.yaml")
    print(strings)
    print(get_str("levels.back"))
