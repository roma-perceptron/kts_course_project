import os


def read_version():
    try:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "..", "VERSION")) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "v0.0.1"


__appname__ = "kts_backend__roma_perceptron"
__version__ = read_version()
