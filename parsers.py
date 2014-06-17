#!/usr/bin/python
# Filename: parsers.py

import argparse #for parsing of argumenets
import sys

def create_parser():
    """Function creates parser of params"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='img')
    parser.add_argument('-f', '--file', default='test.json')

    return parser

parser = create_parser()
namespace = parser.parse_args(sys.argv[1:])
currentpath = format(namespace.directory)  
currentfile = format(namespace.file)

# End of parsers.py    