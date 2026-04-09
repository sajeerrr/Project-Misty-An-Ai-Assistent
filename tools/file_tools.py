import os


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return str(e)


def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "File written"
    except Exception as e:
        return str(e)


def get_current_directory():
    try:
        return os.getcwd()
    except Exception as e:
        return str(e)


def list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return str(e)