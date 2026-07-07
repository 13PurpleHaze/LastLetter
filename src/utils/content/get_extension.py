import os


def get_extension(content: str):
    return os.path.splitext(content)[1].lower().lstrip(".")
