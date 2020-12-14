import yaml

strings = dict()


def init():
    pass


def load(filename: str):
    global strings
    text: str
    with open(filename, encoding='utf-8') as file:
        text = file.read()
        print(text)
    strings = yaml.safe_load(text)


def get_str(string: str, report=False) -> str:
    global strings
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
    # init()
    load("lang/pt-br.yaml")
    print(strings)
    print(get_str("levels.back"))
