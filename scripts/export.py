"""
Command-line script which automates the exporting, munging, cleaning, and saving operations involved in generating
the core dataset of interest in this project.
"""
# TODO: Finish writing this.
from lxml import etree
# from itertools import zip_longest
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


def get_module(table, module_name, xmlpaths):
    """
    Given an XML element representing a table within everything.ndfbin and an attribute Module reference of interest,
    returns that module if it exists and None if it does not.
    """
    map_name = module_name.replace("ModuleDescriptor", "")[1:]
    modules = [module.text for module in table.find("Modules")]
    try:
        selector_module_text = list(filter(lambda module: map_name in module, modules))[0]
        selector_module_id = selector_module_text.split(":")[-1].split(" ")[1]
        selector = xmlpaths['TModuleSelector.xml'].find("TModuleSelector[@id='{0}']".format(selector_module_id))
        pointer_text = selector.find("Default").text
        pointer_id = pointer_text.split(":")[-1].split(" ")[1]
        module = xmlpaths['{0}.xml'.format(module_name)]\
            .find("{0}[@id='{1}']".format(module_name, pointer_id))
        return module
    except IndexError:
        return None



def get_object_reference(table, object):
    pass


def get_object_reference_list(table, object_reference_list):
    pass


def serialize_token(table, attr, lookup):
    """
    Returns a token from a lookup table.
    """
    try:
        token = table.find(attr).text
        return lookup[token]
    except KeyError:
        return None


def serialize_unit(unit, xmlpaths, localization):
    srs = pd.Series()
    ########################
    # TOP-LEVEL ATTRIBUTES #
    ########################
    for attribute in ["_ShortDatabaseName", "ClassNameForDebug", "StickToGround", "ManageUnitOrientation",
                      "HitRollSizeModifier", "IconeType", "PositionInMenu", "AliasName", "Category", "AcknowUnitType",
                      "TypeForAcknow", "Nationalite", "MotherCountry", "ProductionYear", "MaxPacks", "Factory",
                      "ProductionTime", "CoutEtoile", "UnitMovingType", "VitesseCombat", "UpgradeRequire",
                      "IsPrototype", "Key", "HitRollECMModifier"]:
        srs[attribute] = get_attribute(unit, attribute)

    ################
    # IN-GAME NAME #
    ################
    # TODO: Figure out why this doesn't work, because it's critical to have these "real" names available.
    # for attribute in ["NameInMenuToken"]:
    #     srs[attribute] = serialize_token(unit, attribute, localization)

    ###########
    # STEALTH #
    ###########
    visibility = get_module(unit, "TVisibilityModuleDescriptor", xmlpaths)
    srs["UnitStealthBonus"] = get_attribute(visibility, "UnitStealthBonus")

    ########
    # FUEL #
    ########
    fuel = get_module(unit, "TFuelModuleDescriptor", xmlpaths)
    srs["FuelCapacity"] = get_attribute(fuel, "FuelCapacity")
    srs["FuelMoveDuration"] = get_attribute(fuel, "FuelMoveDuration")
    # Return
    return srs


def main():
    fullpath = "{0}/{1}/{2}".format(parser.parse_args().path, parser.parse_args().version,
                                    "pc/ndf/patchable/gfx").replace("/", "\\")
    xmlpaths = dict()
    for root, dirs, files in os.walk(fullpath):
        for name in files:
            xmlpaths[name] = etree.parse(os.path.join(root, name))

    localizationpath = "{0}/{1}/{2}".format(parser.parse_args().path, parser.parse_args().version,
                                     "ZZ_Win/pc/localisation/us/localisation/unites_fixed.csv").replace("/", "\\")
    # import pdb; pdb.set_trace()
    localization = pd.read_csv(localizationpath, encoding='windows-1252').set_index("Hash")
    data = []

    units = xmlpaths['TUniteAuSolDescriptor.xml'].findall("TUniteAuSolDescriptor")
    test = list(units)[:25]
    for unit in tqdm(units):
        data.append(serialize_unit(unit, xmlpaths, localization))
        df = pd.concat(data, axis=1).T
        df.to_csv("../data/510049986/data_dummy.csv")

if __name__ == "__main__":
    main()