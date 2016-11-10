"""
Command-line script which automates the exporting, munging, cleaning, and saving operations involved in generating
the core dataset of interest in this project.
"""
# TODO: Finish writing this.
from lxml import etree
from itertools import zip_longest
from tqdm import tqdm
import pandas as pd
import os


import argparse

parser = argparse.ArgumentParser(description="""
Parse an XML dump of raw Wargame: Red Dragon internal unit value information into a unified CSV file.
""")
parser.add_argument("path", help="A filepath to the folder containing XML dumps to be processed (e.g. "
                                 "C:\\Users\\Alex\\Desktop\\wargame-analysis\\raws).")
parser.add_argument("version", help="The version of Wargame: Red Dragon to be processed (e.g. 510049986). Should be a "
                                    "subfolder of the filepath above, whose contents are generated using the "
                                    "Wargame XML Exporter tool.")
parser.add_argument("output", help="A filepath to the destination folder this script will write its output to.")


def get_attribute(table, attr):
    """
    Given an XML element representing a table within everything.ndfbin and an attribute of interest, returns the
    contents of that attribute.
    """
    # import pdb; pdb.set_trace()
    return table.find(attr).text


def get_collection(table, attr):
    """
    Given an XML element representing a table within everything.ndfbin and an attribute Collection of interest,
    returns the contents of that attribute's Collection.
    """
    elements = table.find(attr)
    values = [element.text for element in elements]
    return values


def serialize_unit(unit):
    srs = pd.Series()
    for attribute in ["_ShortDatabaseName", "ClassNameForDebug", "StickToGround", "ManageUnitOrientation",
                      "HotRollSizeModifier", "IconeType", "PositionInMenu", "AliasName", "Category", "AknowUnitType",
                      "TypeForAcknow", "Nationalite", "MotherCountry", "ProductionYear", "MaxPacks", "Factory",
                      "ProductionTime", "CoutEtoile", "UnitMovingType", "VitesseCombat", "UpgradeRequire",
                      "IsPrototype", "Key", "HitRollECMModifier"]:
        srs[attribute] = get_attribute(unit, attribute)
    return srs


def main():
    fullpath = "{0}/{1}/{2}".format(parser.parse_args().path, parser.parse_args().version,
                                    "NDF_Win/pc/ndf/patchable/gfx").replace("/", "\\")
    xmlpaths = dict()
    for root, dirs, files in os.walk(fullpath):
        for name in files:
            xmlpaths[name] = etree.parse(os.path.join(root, name))

    # localizationpath = "{0}/{1}/{2}".format(parser.parse_args().path, parser.parse_args().version,
    #                                  "ZZ_Win/pc/localisation/us/localisation/unites.csv").replace("/", "\\")
    # localization = pd.read_csv(localizationpath, encoding='utf-8')
    data = []

    units = xmlpaths['TUniteAuSolDescriptor.xml'].findall("TUniteAuSolDescriptor")
    test = list(units)[:25]
    for unit in tqdm(test):
        data.append(serialize_unit(unit))
        df = pd.concat(data, axis=1).T
        df.to_csv("../data/510049986/data_dummy.csv")

if __name__ == "__main__":
    main()