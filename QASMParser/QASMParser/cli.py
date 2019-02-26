import argparse

parser = argparse.ArgumentParser(description='QASM parser to translate from QASM to QuEST input', add_help=True)
parser.add_argument('sources', nargs=argparse.REMAINDER, help="List of sources to compile")
parser.add_argument('-o','--output', help="File to compile to")
parser.add_argument('-l','--language', help="Output file language")

def get_command_args():
    return parser.parse_args()
