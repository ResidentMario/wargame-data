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


def get_id(table):
    return table.items()[0][1]


def get_attribute(table, attr):
    """
    Given an XML element representing a table within everything.ndfbin and an attribute of interest, returns the
    contents of that attribute.
    """
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
        pointer_kind = pointer_text.split(":")[-1].split(" ")[-1]
        module = xmlpaths['{0}.xml'.format(pointer_kind)]\
            .find("{0}[@id='{1}']".format(pointer_kind, pointer_id))
        # import pdb; pdb.set_trace()
        return module
    except IndexError:
        return None


def get_object_reference(table, attr, xmlpaths):
    """
    Given an XML element representing a table within everything.ndfbin and an attribute containing a reference to
    another table, returns the XML element representing that table.

    This is distinct from get_module, above, which must handle two levels of indirection.
    """
    try:
        module_id = table.find(attr).text.split(":")[-1].split(" ")[1]
    except IndexError:
        return None
    module_name = table.find(attr).text.split(":")[-1].split(" ")[-1]
    module = xmlpaths['{0}.xml'.format(module_name)] \
        .find("{0}[@id='{1}']".format(module_name, module_id))
    return module


# TODO: Implement.
def get_module_of_kind(table, module_name, kinds, xmlpaths):
    """
    This method is a modification of get_module which additionally takes a "kinds" parameter. The "kinds" corresponds
    with a
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


def get_object_reference_list(table, attr, xmlpaths):
    """
    Same as get_object_reference, but applies to a list of them.
    """
    objects = get_collection(table, attr)
    ret = []
    # import pdb; pdb.set_trace()
    for object in objects:
        module_id = object.split(":")[-1].split(" ")[1]
        module_name = object.split(":")[-1].split(" ")[-1]
        module = xmlpaths['{0}.xml'.format(module_name)] \
            .find("{0}[@id='{1}']".format(module_name, module_id))
        ret.append(module)
    return ret


def get_token(table, attr, lookup):
    """
    Returns a token from a lookup table.
    """
    hash = get_attribute(table, attr)
    return lookup[lookup['Hash'] == hash].iloc[0]['String']


def serialize_unit(unit, xmlpaths, localization):
    srs = pd.Series()

    ######
    # ID #
    ######
    srs['ID'] = get_id(unit)

    ########################
    # TOP-LEVEL ATTRIBUTES #
    ########################
    for attr in ["_ShortDatabaseName", "ClassNameForDebug", "StickToGround", "ManageUnitOrientation",
                      "HitRollSizeModifier", "IconeType", "PositionInMenu", "AliasName", "Category", "AcknowUnitType",
                      "TypeForAcknow", "Nationalite", "MotherCountry", "ProductionYear", "MaxPacks", "Factory",
                      "ProductionTime", "CoutEtoile", "UnitMovingType", "VitesseCombat", "IsPrototype", "Key",
                      "HitRollECMModifier"]:
        srs[attr] = get_attribute(unit, attr)
    for attr in ["ProductionPrice", "MaxDeployableAmount", "ShowInMenu", "UnitTypeTokens"]:
        srs[attr] = get_collection(unit, attr)
    # import pdb; pdb.set_trace()
    upgrade_path = get_object_reference(unit, "UpgradeRequire", xmlpaths)
    if upgrade_path is not None:
        srs["UpgradeRequired"] = get_id(upgrade_path)
    death_explosion = get_object_reference(unit, "DeathExplosionAmmo", xmlpaths)
    if death_explosion is not None:
        srs["DeathExplosionID"] = get_id(death_explosion)
        for attr in ["SuppressDamages", "RadiusSplashSuppressDamages", "Arme", "RadiusSplashPhysicalDamages"]:
            srs["DeathExplosion{0}".format(attr)] = get_attribute(death_explosion, attr)

    ################
    # IN-GAME NAME #
    ################
    srs["NameInMenuToken"] = get_attribute(unit, "NameInMenuToken")
    srs["NameInMenu"] = get_token(unit, "NameInMenuToken", localization)

    ########
    # TYPE #
    ########
    unit_type = get_module(unit, "TTypeUnitModuleDescriptor", xmlpaths)
    for attr in ["TypeUnitValue", "UnitInfoJaugeType", "Training", "NameInMenuToken", "CIWS", "Sailing"]:
        srs[attr] = get_attribute(unit_type, attr)
    # The "Filters" field is not recoverable because it is not exported properly in the XML.

    ############
    # POSITION #
    ############
    position = get_module(unit, "TPositionDescriptor", xmlpaths)
    if position is not None:
        for attr in ["LowAltitudeFlyingAltitude", "NearGroundFlyingAltitude"]:
            srs[attr] = get_attribute(position, attr)

    ##############
    # EXPERIENCE #
    ##############
    experience = get_module(unit, "TModernWarfareExperienceModuleDescriptor", xmlpaths)
    if experience is not None:
        for attr in ["CanWinExperience", "ExperienceGainBySecond", "KillExperienceBonus"]:
            srs[attr] = get_attribute(experience, attr)

    ###########
    # COMMAND #
    ###########
    command = get_module(unit, "TCommandManagerModuleDescriptor", xmlpaths)
    if command is not None:
        srs["IsCommandUnit"] = True

    #
    # SKIP: TScannerModuleDescriptor, TScannerConfigurationDescriptor
    # TODO: ^^^.
    #

    ########
    # FUEL #
    ########
    fuel = get_module(unit, "TFuelModuleDescriptor", xmlpaths)
    if fuel is not None:
        srs["FuelCapacity"] = get_attribute(fuel, "FuelCapacity")
        srs["FuelMoveDuration"] = get_attribute(fuel, "FuelMoveDuration")

    ############
    # MOVEMENT #
    ############
    movement = get_module(unit, "MouvementHandler", xmlpaths)
    movement_kind = movement.tag
    if "LandVehicle" in movement_kind:
        for attr in ["Maxspeed", "UnitMovingType", "SpeedBonusOnRoad", "TempsDemiTour", "MaxAcceleration",
                     "MaxDeceleration", "VehicleSubType", "TerrainsToIgnoreMask"]:
            srs[attr] = get_attribute(movement, attr)
    elif "Helicopter" in movement_kind:
        for attr in ["Maxspeed", "MaxAcceleration", "MaxDeceleration", "UnitMovingType", "CyclicManoeuvrability",
                     "GFactorLimit", "LateralSpeed", "Mass", "MaxInclination", "RotorArea", "TorqueManoeuvrability",
                     "UpwardsSpeed", "TempsDemiTour"]:
            srs[attr] = get_attribute(movement, attr)
    elif "Airplane" in movement_kind:
        for attr in ["Maxspeed", "UnitMovingType", "FlyingAltitude", "MinimalAltitude", "GunMuzzleSpeed"]:
            srs[attr] = get_attribute(movement, attr)

    # TODO: Transportable

    ##########
    # SUPPLY #
    ##########
    supply = get_module(unit, "TSupplyModuleDescriptor", xmlpaths)
    if supply is not None:
        for attr in ["SupplyCapacity", "DeploymentDuration", "WithdrawalDuration", "SupplyPriority"]:
            srs[attr] = get_attribute(supply, attr)

    ###########
    # WEAPONS #
    ###########
    weapon_manager = get_module(unit, "TWeaponManagerModuleDescriptor", xmlpaths)
    for attr in ["SalvoIsMainSalvo", "Salves"]:
        srs[attr] = get_attribute(weapon_manager, attr)
    weapons = []
    for turret in get_object_reference_list(weapon_manager, "TurretDescriptorList", xmlpaths):
        turret_kind = turret.tag
        for weapon in get_object_reference_list(turret, "MountedWeaponDescriptorList", xmlpaths):
            weapon_srs = pd.Series()
            # First pick up all of the turret-level info for this weapon.
            if "TwoAxis" in turret_kind:
                for attr in ["Tag", "TagIndex", "VitesseRotation", "AngleRotationMax", "AngleRotationMaxPitch",
                             "AngleRotationBasePitch", "AngleRotationMinPitch", "AngleRotationBase"]:
                    weapon_srs[attr] = get_attribute(turret, attr)
            elif "TurretUnit" in turret_kind:
                for attr in ["Tag", "TagIndex", "AngleRotationMax", "AngleRotationMaxPitch",
                             "AngleRotationMinPitch"]:
                    weapon_srs[attr] = get_attribute(turret, attr)
            elif "TurretBombardier" in turret_kind:
                for attr in ["FlyingAltitude", "FlyingSpeed"]:
                    weapon_srs[attr] = get_attribute(turret, attr)
            elif "TurretInfanterie" in turret_kind:
                pass  # No variables of interest.
            # Then pick up the weapon-level variables.
            for attr in ["SalvoStockIndex", "SalvoStockIndex_ForInterface", "TirEnMouvement", "TirContinu",
                         "AnimateOnlyOneSoldier"]:
                weapon_srs[attr] = attr
            # The pick up the ammunition-level variables.
            ammo = get_object_reference(weapon, "Ammunition", xmlpaths)
            for attr in ["Arme", "ProjectileType", "Puissance", "TempsEntreDeuxTirs", "TempsEntreDeuxFx",
                         "PorteeMaximale", "PorteeMaximaleBateaux", "AngleDispersion", "RadiusSplashSuppressDamages",
                         "SuppressDamages", "RayonPinned", "TirIndirect", "TirReflexe", "TempsEntreDeuxSalves",
                         "NbrProjectilesSimultanes", "NbTirParSalves", "AffichageMunitionParSalve", "Level",
                         "FireDescriptor", "FireTriggeringProbability", "RadiusSplashPhysicalDamages",
                         "PhysicalDamages", "WeaponCursorType", "PorteeMinimale", "PorteeMinimaleBateaux",
                         "DispersionAtMinRange", "DispersionAtMaxRange", "NoiseDissimulationMalus", "TempsDeVisee",
                         "AffichageMenu", "SupplyCost", "SmokeDescriptor", "PorteeMaximaleTBA", "PorteeMinimaleTBA",
                         "PorteeMaximaleHA", "MissileTimeBetweenCorrections", "Guidance", "EfficaciteSelonPortee",
                         "AffecteParNombre", "NeedModelChange", "IsFireAndForget", "IgnoreInflammabilityConditions",
                         "InterdireTirReflexe", "CorrectedShotDispersionMultiplier", "IsSubAmmunition",
                         "RandomDispersion", "TempsAnimation", "PorteeMaximaleProjectile",
                         "PorteeMinimaleProjectile", "PorteeMinimaleHA"]:
                weapon_srs[attr] = get_attribute(ammo, attr)
            acc = get_object_reference(ammo, "HitRollRule", xmlpaths)
            for attr in ["MinimalHitProbability", "MinimalCritProbability", "HitProbability",
                         "HitProbabilityWhileMoving"]:
                weapon_srs[attr] = get_attribute(acc, attr)
            # Add the weapon to the list.
            weapons.append(weapon_srs)
        # Attach all of the weapons to the dataset!
        for i, weapon in enumerate(weapons, start=1):
            weapons[i - 1].index = ["Weapon{0}{1}".format(i, attr) for attr in weapons[i - 1].index]
            # import pdb; pdb.set_trace()
            srs = srs.append(weapon)


    ##########
    # DAMAGE #
    ##########
    damage = get_module(unit, "TModernWarfareDamageModuleDescriptor", xmlpaths)
    if damage is not None:
        for attr in ["MaxDamages", "AutoOrientation", "Transporter", "IsTargetableAsBoat"]:
            srs[attr] = get_attribute(damage, attr)
        common_damage = get_object_reference(damage, "CommonDamageDescriptor", xmlpaths)
        for attr in ["StunDamagesRegen", "StunDamagesToGetStunned", "SuppressDamagesRegenRatioOutOfRange",
                     "MaxSuppressionDamages"]:
            srs[attr] = get_collection(common_damage, attr)
        for attr in ["PaliersSuppressDamages", "PaliersPhysicalDamages"]:
            srs[attr] = get_collection(common_damage, attr)
        armor = get_object_reference(common_damage, "BlindageProperties", xmlpaths)
        for side in ["Front", "Sides", "Rear", "Top"]:
            a = get_attribute("BaseBlindage", get_object_reference(armor, "ArmorDescriptor{0}".format(side), xmlpaths))
            srs["Armor{0}".format(side)] = a


    ###########
    # STEALTH #
    ###########
    visibility = get_module(unit, "TVisibilityModuleDescriptor", xmlpaths)
    srs["UnitStealthBonus"] = get_attribute(visibility, "UnitStealthBonus")

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
    localization = pd.read_csv(localizationpath, encoding='windows-1252', index_col=0)
    data = []

    units = xmlpaths['TUniteAuSolDescriptor.xml'].findall("TUniteAuSolDescriptor")
    # test = list(units)[:25]
    for unit in tqdm(units):
        data.append(serialize_unit(unit, xmlpaths, localization))
        df = pd.concat(data, axis=1).T
        df.to_csv("../data/510049986/data_dummy.csv")

if __name__ == "__main__":
    main()