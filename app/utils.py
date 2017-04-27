import json

def find_graze():
    import sys
    from os import path

    dirname = path.abspath(path.dirname(path.abspath(__file__)))

    with open(path.join(dirname, 'config.json')) as json_data:
        graze_path = json.load(json_data)['graze_path']

    sys.path.append(path.join(dirname, graze_path))
