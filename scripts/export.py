"""
Command-line script which automates the exporting, munging, cleaning, and saving operations involved in generating
the core dataset of interest in this project.
"""
# TODO: Finish writing this.
from lxml import etree
from itertools import zip_longest
from tqdm import tqdm
import pandas as pd


import argparse

parser = argparse.ArgumentParser(description="""
Parse an XML dump of raw Wargame: Red Dragon internal unit value information into a unified CSV file.
""")
parser.add_argument("path", help="A filepath to the folder containing XML dump to be processed.")
parser.add_argument("output", help="A filepath to the destination folder this script will write its output to.")

def main():
    data = []
    for unit in tqdm(tunits.findall("TUniteAuSolDescriptor")):
        data.append(serialize_unit(unit))
        df = pd.concat(data, axis=1).T
        df.to_csv("../data/510049986/data.csv")

if __name__ == "__main__":
    main()