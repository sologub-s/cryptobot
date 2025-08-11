import re
import os

def slugify(filename: str) -> str:
    name, _ = os.path.splitext(filename)
    name = re.sub(r'[^a-zA-Z0-9]+', '-', name)
    return name.strip('-').lower()