import json

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError as e:
        print(f"No such file or directory, please verify your input. {e.filename}")
        exit()