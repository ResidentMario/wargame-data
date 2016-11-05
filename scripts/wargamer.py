"""
Command-line script which automates the exporting, munging, cleaning, and saving operations involved in generating
the core dataset of interest in this project.
"""
# TODO: Finish writing this.
from lxml import etree
from itertools import zip_longest
from tqdm import tqdm
import pandas as pd


tunits = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TUniteAuSolDescriptor.xml")
weapon_managers = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TWeaponManagerModuleDescriptor.xml")
module_selectors = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TModuleSelector.xml")
turrets = {
    'TTurretUnitDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TTurretUnitDescriptor.xml"),
    'TTurretInfanterieDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TTurretInfanterieDescriptor.xml"),
    'TTurretTwoAxisDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TTurretTwoAxisDescriptor.xml"),
    'TTurretBombardierDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TTurretBombardierDescriptor.xml")
}
weapon_descriptors = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TMountedWeaponDescriptor.xml")
ammunition = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TAmmunition.xml")
fuel_xml = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TFuelModuleDescriptor.xml")
movements = {
    'TMouvementHandlerLandVehicleDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TMouvementHandlerLandVehicleDescriptor.xml"),
    'TMouvementHandlerHelicopterDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TMouvementHandlerHelicopterDescriptor.xml"),
    'TMouvementHandlerAirplaneDescriptor': etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TMouvementHandlerAirplaneDescriptor.xml"),
}
damage = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TModernWarfareDamageModuleDescriptor.xml")
visibilities = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TVisibilityModuleDescriptor.xml")
experiences = etree.parse("../raws/510049986/NDF_Win/pc/ndf/patchable/gfx/everything/TModernWarfareExperienceModuleDescriptor.xml")
numbers_in_letters = {
    1: 'One',
    2: 'Two',
    3: 'Three',
    4: 'Four',
    5: 'Five'
}


def serialize_unit(tunit_xml):
    id = tunit_xml.items()[0][1]
    unit = pd.Series()
    unit['UnitDescriptorID'] = id
    for tunit_element in tunit_xml:
        tag = tunit_element.tag
        # The complex case.
        if tag == "Modules":
            # Find the WeaponManager module ID.
            modules = [collectionelement.text for collectionelement in tunit_element]
            try:
                weapon_manager_text = list(filter(lambda module: "WeaponManager" in module, modules))[0]
                unit['WeaponManagerModuleSelectorID'] = weapon_manager_text.split(":")[-1].split(" ")[1]
                # Recursively pass it to serialize_weapon_manager.
                unit = serialize_weapon_manager(unit)
            except IndexError:
                # No WeaponManager module is attached to this unit.
                # This happens when the unit is a supply unit, for example.
                # In that case, there's nothing else to see! We can just return the unit as-is at the end of this op.
                pass

            # Find and extract the Fuel module. Note that many units, e.g. infantry, don't need fuel.
            try:
                fuel_text = list(filter(lambda module: "Fuel" in module, modules))[0]
                unit['FuelModuleSelectorID'] = fuel_text.split(":")[-1].split(" ")[1]
                unit = serialize_fuel(unit)
            except:
                pass

            # Find and extract the Movement module.
            movement_text = list(filter(lambda module: "Mouvement" in module, modules))[0]
            movement_selector_id = movement_text.split(":")[-1].split(" ")[1]
            unit['MovementSelectorID'] = movement_selector_id
            serialize_movement(unit)

            # Find and extract the Damage module.
            damage_text = list(filter(lambda module: "Damage" in module, modules))[0]
            damage_selector_id = damage_text.split(":")[-1].split(" ")[1]
            unit['DamageSelectorID'] = damage_selector_id
            serialize_damage(unit)

            # Find and extract the Visibility module.
            visibility_text = list(filter(lambda module: "Visibility" in module, modules))[0]
            visibility_selector_id = visibility_text.split(":")[-1].split(" ")[1]
            unit['VisibilitySelectorID'] = visibility_selector_id
            serialize_visibility(unit)

            # Find and extract the Experience module.
            experience_text = list(filter(lambda module: "Experience" in module, modules))[0]
            experience_selector_id = experience_text.split(":")[-1].split(" ")[1]
            unit['ExperienceSelectorID'] = experience_selector_id
            serialize_experience(unit)

        # All other cases are simple.
        elif tag == "ProductionPrice":
            production_prices = [collectionelement.text for collectionelement in tunit_element]
            # e.g. production_prices = [90, 15, 15, 15, 15].
            # This structure seems to allow variation of price based on veterancy, but this feature is not used in-game.
            # In certain cases, the production price is simply "null". In that case `production_prices` will at this
            # point be an empty list (when is production price null? Well the NATO and PACT barges are null for example).
            if len(production_prices) > 0:
                actual_price = production_prices[0]
            else:
                actual_price = "null"
            unit['ProductionPrice'] = actual_price
        elif tag == "MaxDeployableAmount":
            deployable_amounts = [collectionelement.text for collectionelement in tunit_element]
            for i, vet_availability in enumerate(['RookieDeployableAmount', 'TrainedDeployableAmount',
                                                  'HardenedDeployableAmount', 'VeteranDeployableAmount',
                                                  'EliteDeployableAmount']):
                unit[vet_availability] = deployable_amounts[i]
        # Ignore junk group tags
        elif tag in ["ShowInMenu", "UnitTypeTokens"]:
            pass
        else:
            val = tunit_element.text
            unit[tag] = val
    if 'CanDeploySmoke' not in unit.index:
        unit['CanDeploySmoke'] = False
    return unit


def serialize_weapon_manager(unit):
    # First we have to break through the module_selector element containing a reference to our desired
    # weapon_manager element.
    selector = module_selectors.find("TModuleSelector[@id='{0}']".format(unit['WeaponManagerModuleSelectorID']))
    selector_id = selector.items()[0][1]
    unit['WeaponManagerModuleSelectorID'] = selector_id  # Could come in handy later.
    weapon_manager_pointer_text = selector.find("Default").text
    weapon_manager_module_selector_id = weapon_manager_pointer_text.split(":")[-1].split(" ")[1]
    weapon_manager = weapon_managers.find("TWeaponManagerModuleDescriptor[@id='{0}']" \
                                          .format(weapon_manager_module_selector_id))
    weapon_manager_id = weapon_manager.items()[0][1]
    unit['WeaponManagerID'] = weapon_manager_id  # Store this too.
    # Now that we have the weapon_manager, we parse it.
    for wm_element in weapon_manager:
        tag = wm_element.tag
        # Complex case: a turret; in which case we regress again.
        if tag == "TurretDescriptorList":
            turret_ids = [collectionelement.text.split(":")[-1].split(" ")[1] for collectionelement in wm_element]
            turret_types = [collectionelement.text.split(":")[-1].split(" ")[-1] for collectionelement in wm_element]
            # First though store the turret IDs and types, because why not.
            for modifier, turret_id in zip_longest(['One', 'Two', 'Three'], turret_ids):
                unit['Turret{0}ID'.format(modifier)] = turret_id
            for modifier, turret_type in zip_longest(['One', 'Two', 'Three'], turret_types):
                unit['Turret{0}Type'.format(modifier)] = turret_type
            unit = serialize_turrets(unit)
        elif tag == "Salves":
            salvos = [collectionelement.text for collectionelement in wm_element]
            for i, wep_salvos in enumerate(['SalvosWeaponOne', 'SalvosWeaponTwo', 'SalvosWeaponThree']):
                unit[wep_salvos] = salvos[i]
        elif tag == "SalvoIsMainSalvo":
            salvo_mains = [collectionelement.text for collectionelement in wm_element]
            for i, wep_salvo_m in enumerate(['SalvoWeaponOneIsMain', 'SalvoWeaponTwoIsMain', 'SalvoWeaponThreeIsMain']):
                unit[wep_salvo_m] = salvo_mains[i]
        else:
            # Ignore other elements because they are redundant:
            # HasMainSalvo, ControllerName, _ShortDatabaseName
            pass
    return unit


def serialize_turrets(unit):
    for modifier, turret_id in zip(['One', 'Two', 'Three'], ['Turret{0}ID'.format(n) for n in ['One', 'Two', 'Three']]):
        # If no turret, jump back to the top of the loop.
        if not unit[turret_id]:
            continue
        # Otherwise, nab the correct turret XML.
        turret_type = unit['Turret{0}Type'.format(modifier)]
        turret_xml = turrets[turret_type]
        turret = turret_xml.find("{0}[@id='{1}']".format(turret_type, unit[turret_id]))
        # Now remember that we want to try and remove information dependency based on turret placement from the
        # final CSV, in order to flatten this unfamilair level of heirarchy.
        # In order to do that, we will replicate turret information across all weapons.
        # In order to do THAT we need to create a turret frame equally valid for all weapons on that turret.
        turret_srs = pd.Series()
        for element in turret:
            tag = element.tag
            if tag != "MountedWeaponDescriptorList":
                turret_srs[tag] = element.text
        # Now we are ready to recurse to the mounted weapon level.
        mounted_weapons = turret.find("MountedWeaponDescriptorList")
        mounted_weapon_ids = []
        for mounted_weapon in mounted_weapons:
            mounted_weapon_id = mounted_weapon.text.split(":")[-1].split(" ")[1]
            mounted_weapon_ids.append(mounted_weapon_id)
            serialize_weapon(unit, turret_srs, len(mounted_weapon_ids), mounted_weapon_id)
    return unit


def serialize_weapon(unit, turret_srs, weapon_number,
                     # weapon_number is the # of this wep in the unit's list of them...
                     weapon_index):  # ...whilst weapon_index is the full database index of the weapon.
    weapon_descriptor = weapon_descriptors.find("TMountedWeaponDescriptor[@id='{0}']".format(weapon_index))
    for element in weapon_descriptor:
        tag = element.tag
        # Complex case, dive in one final time...
        if tag == "Ammunition":
            tammunition_id = element.text.split(":")[-1].split(" ")[1]
            unit["Weapon{0}AmmunitionID".format(numbers_in_letters[weapon_number])] = tammunition_id
            unit = serialize_ammo(unit, tammunition_id, weapon_number, turret_srs)
        # Ignore.
        elif tag == "EffectTag":
            pass
        # Simple case, append.
        else:
            unit["Weapon{0}{1}".format(numbers_in_letters[weapon_number], tag)] = element.text
    return unit


def serialize_ammo(unit, tammunition_id, weapon_number, turret_srs):
    ammo = ammunition.find("TAmmunition[@id='{0}']".format(tammunition_id))
    # We want to pay particular attention to a case in which a unit may have a weapon doing double duty:
    # it can both shoot and smoke. This clouds things, since the smoking rounds get their own TAmmunition instance
    # in the weapons list, knocking off our one-to-one of each weapon corresponding to its corresponding weapon,
    # numerically, on the weapon cards.
    #
    # To account for this, let check to see that the ammunition we are examining deals suppression damage. If it
    # does not, then it must be a smoke round, and we can handle that as a special case.
    # Note that in the negative case, this requires attaching a CanDeploySmoke of False at the last step before
    # returning at the very top of the loop, in serialize_unit.
    if ammo.find("SuppressDamages").text == "null":
        unit['CanDeploySmoke'] = True
        return unit
    for element in ammo:
        unit["Weapon{0}{1}".format(numbers_in_letters[weapon_number], element.tag)] = element.text
    unit = pd.concat([unit, turret_srs.reindex(
        ["Weapon{0}{1}".format(numbers_in_letters[weapon_number], ind) for ind in turret_srs.index])])
    return unit


# Now onto auxiliaries
def serialize_fuel(unit):
    selector = module_selectors.find("TModuleSelector[@id='{0}']".format(unit['FuelModuleSelectorID']))
    fuel_module_id = selector.find("Default").text.split(":")[-1].split(" ")[1]
    fuel_element = fuel_xml.find("TFuelModuleDescriptor[@id='{0}']".format(fuel_module_id))
    unit['FuelCapacity'] = fuel_element.find("FuelCapacity").text
    unit['FuelMoveDuration'] = fuel_element.find('FuelMoveDuration').text
    return unit


def serialize_movement(unit):
    selector = module_selectors.find("TModuleSelector[@id='{0}']".format(unit['MovementSelectorID']))
    movement_module_id = selector.find("Default").text.split(":")[-1].split(" ")[1]
    movement_module_kind = selector.find("Default").text.split(":")[-1].split(" ")[-1]
    unit['MovementModuleID'] = movement_module_id
    unit['MovementType'] = movement_module_kind
    movement_element = movements[movement_module_kind].find(
        "{0}[@id='{1}']".format(movement_module_kind, movement_module_id))
    for variable_of_interest in ['Maxspeed', 'UnitMovingType', 'FlyingAltitude', 'MinimalAltitude', 'GunMuzzleSpeed',
                                 # plane
                                 'CyclicManoeuvrability', 'GFactorLimit', 'LateralSpeed', 'Mass', 'MaxInclination',
                                 'RotorArea', 'TorqueManoeuvrability', 'UpwardsSpeed', 'TempsDemiTour',
                                 'MaxAcceleration', 'MaxDeceleration', 'WeaponSabordAngle',  # helo
                                 'SpeedBonusOnRoad', 'VehicleSubType', 'TerrainsToIgnoreMask']:  # land
        try:
            unit[variable_of_interest] = movement_element.find(variable_of_interest).text
        except:
            unit[variable_of_interest] = None
    return unit


def serialize_damage(unit):
    selector = module_selectors.find("TModuleSelector[@id='{0}']".format(unit['DamageSelectorID']))
    damage_module_id = selector.find("Default").text.split(":")[-1].split(" ")[1]
    unit['DamageModuleID'] = damage_module_id
    damage_element = damage.find("TModernWarfareDamageModuleDescriptor[@id='{0}']".format(damage_module_id))
    unit['MaxDamages'] = damage_element.find("MaxDamages").text
    unit['MaxHPForHUD'] = damage_element.find('MaxHPForHUD').text
    unit['AutoOrientation'] = damage_element.find("AutoOrientation").text
    unit['Transporter'] = damage_element.find('Transporter').text
    unit['IsTargetableAsBoat'] = damage_element.find("IsTargetableAsBoat").text


def serialize_visibility(unit):
    selector = module_selectors.find("TModuleSelector[@id='{0}']".format(unit['VisibilitySelectorID']))
    visibility_module_id = selector.find("Default").text.split(":")[-1].split(" ")[1]
    unit['VisibilityModuleID'] = visibility_module_id
    visibility_element = visibilities.find("TVisibilityModuleDescriptor[@id='{0}']".format(visibility_module_id))
    unit['UnitStealthBonus'] = visibility_element.find("UnitStealthBonus").text


def serialize_experience(unit):
    selector = module_selectors.find("TModuleSelector[@id='{0}']".format(unit['ExperienceSelectorID']))
    experience_module_id = selector.find("Default").text.split(":")[-1].split(" ")[1]
    unit['ExperienceModuleID'] = experience_module_id
    experience_element = experiences.find(
        "TModernWarfareExperienceModuleDescriptor[@id='{0}']".format(experience_module_id))
    unit['ExperienceGainBySecond'] = experience_element.find("ExperienceGainBySecond").text
    unit['KillExperienceBonus'] = experience_element.find("KillExperienceBonus").text
    unit['CanWinExperience'] = experience_element.find("CanWinExperience").text


def main():
    data = []
    for unit in tqdm(tunits.findall("TUniteAuSolDescriptor")):
        data.append(serialize_unit(unit))
        df = pd.concat(data, axis=1).T
        df.to_csv("../data/510049986/data.csv")

if __name__ == "__main__":
    main()