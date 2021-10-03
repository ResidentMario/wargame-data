import pandas as pd
import numpy as np
import re
import argparse


parser = argparse.ArgumentParser(description="""
Parse an intermediate Wargame: Red Dragon data file into a finished product.
""")
parser.add_argument("path", help="A filepath to the folder containing XML dumps to be processed (e.g. "
                                 "C:\\Users\\Alex\\Desktop\\wargame-analysis\\raws).")
parser.add_argument("version", help="The version of Wargame: Red Dragon to be processed (e.g. 510049986). Should be a "
                                    "subfolder of the filepath above.")
parser.add_argument("wargame", help="Pass")


def main():
    # Initial load.
    units = pd.read_csv(parser.parse_args().wargame + "/" + parser.parse_args().version + "/raw_data.csv",
                        encoding="windows-1252",
                        index_col=0)
    units = units[~units.apply(lambda srs: 'Deprec!' in srs['NameInMenu'], axis='columns')]
    units = units[~units.apply(lambda srs: 'DEPREC' in srs['NameInMenu'], axis='columns')]

    # Weapon maps.
    def weaponify(unit):
        # We're going to build a new pandas Series with all of the information we want.
        srs = pd.Series()

        # First thing first, how many weapons are we talking about? A quick regex will get us this fact.
        try:
            top_weapon_number = max([int(re.search(r'\d+', c).group()) for c in unit.index \
                                     if ("Weapon" in c) and (pd.notnull(unit[c]))])
        except ValueError:
            # There are none!
            top_weapon_number = 0

        # Some things we need to keep track of outside of the loop.
        salvo_stock_indices_already_visited = []

        for i in range(1, top_weapon_number + 1):
            #         import pdb; pdb.set_trace()

            fragment = 'Weapon{0}'.format(i)
            salvo_index = 0 if unit[fragment + 'SalvoStockIndex'] == "null" else int(unit[fragment + 'SalvoStockIndex'])

            # If we haven't already visited this stock index, this weapon is the first one there.
            # Let's copy its data into our new Series!
            if salvo_index not in salvo_stock_indices_already_visited:
                columns_of_interest = [c for c in unit.index if fragment in c]
                for c in columns_of_interest:
                    srs[c] = unit[c]
            # If we have already visited this stock index, let's find out why.
            else:
                # Before we begin, let's find that previous weapon.
                # We can find it by taking the index of the previous weapon's position in the visited list and
                # adding one.
                previous_fragment = "Weapon{0}".format(salvo_stock_indices_already_visited.index(salvo_index) + 1)

                # Case 1: The new (current) weapon is a smoke weapon.
                # We see this when Arme == 3 and PhysicalDamages is "null".
                if (unit[fragment + 'Arme'] == "null" or int(unit[fragment + 'Arme']) == 3) \
                        and (unit[fragment + 'PhysicalDamages'] == "null"):
                    # Attach a can-smoke tag to the weapon.
                    srs[previous_fragment + 'CanSmoke'] = True
                # Case 2a: The first weapon is an SMG, and the second weapon is also an SMG.
                # SMGs get doubled accuracy when the fight is in CQC. It turns out that this is implemented within the
                # engine by, no joke, simply attaching another copy of the weapon to the unit which points to the same
                # exact thing except that accuracy is doubled.
                #
                # For an example, refer to the French Groupe Commandat command infantry unit, which is the 15th unit
                # in the list of them on the Modding Suite (at the moment at least).
                #
                # To detect this case, we check to see if both weapons are SMGs.
                #
                # Case 2b: Similarly, if the the weapon is a battle rifle, expect half accuracy in CQC.
                # Case: 2c: If the weapon is an assault rifle, expect the same accuracy. But the weapon gets split
                # anyway!
                elif (unit[fragment + 'TypeArme'] == "D1D5010000000000" \
                              and unit[previous_fragment + 'TypeArme'] == "D1D5010000000000") or \
                        (unit[fragment + 'TypeArme'] == "6ABCBA1C00000000" \
                                 and unit[previous_fragment + 'TypeArme'] == "6ABCBA1C00000000") or \
                        (unit[fragment + 'TypeArme'] == "5C99C7BA89E30B00" \
                                 and unit[previous_fragment + 'TypeArme'] == "5C99C7BA89E30B00"):
                    # In this case we do...nothing! The data is already there.
                    pass
                # Case 3: The new (current) weapon is the HE or AP component of the previous weapon.
                # These can occur in either order, so we have to make sense of it by looking at what the values are.
                # Taking a maximum does the job nicely, but first we have to fix nullity.
                else:
                    # Then, we play the game.
                    prior_arme = srs[previous_fragment + 'Arme']
                    if prior_arme == 'null': prior_arme = np.nan
                    curr_arme = unit[fragment + 'Arme']
                    if curr_arme == 'null': curr_arme = np.nan
                    prior_physical = unit[previous_fragment + 'PhysicalDamages']
                    if prior_physical == 'null': prior_physical = np.nan
                    curr_physical = unit[fragment + 'PhysicalDamages']
                    if curr_physical == 'null': curr_physical = np.nan
                    # The rathered tortured semantics are necessary to work around numpy bitching about types.
                    arme = int(np.nanmax(np.array([prior_arme, curr_arme]).astype(float)))
                    physical = int(np.nanmax(np.array([prior_physical, curr_physical]).astype(float)))
                    # Attach the new values.
                    srs[previous_fragment + 'Arme'] = arme
                    srs[previous_fragment + 'PhysicalDamages'] = physical

            # Finally, don't forget to add the stock index to the visited list!
            salvo_stock_indices_already_visited.append(salvo_index)

        # We may have produced empties along the way, populating fields in a pattern like ['Weapon1', 'Weapon3']
        # instead of e.g. ['Weapon1', 'Weapon2']. This is much easier to fix afterwards, though, then during. So
        # let's fix that now! Start with the same regex as before...
        try:
            top_weapon_number = max([int(re.search(r'\d+', c).group()) for c in srs.index \
                                     if ("Weapon" in c) and (pd.notnull(srs[c]))])
        except:
            return srs

        # Assuming we have weapons at all (the duck test above caught the case that we don't), we keep going.
        attached_weapon_numbers = [i for i in range(1, top_weapon_number + 1) if 'Weapon{0}Arme'.format(i) in srs.index]

        # Figure out how to map the attached weapon numbers.
        trips = zip(attached_weapon_numbers, range(1, len(attached_weapon_numbers) + 1))

        # Map down.
        for origin, destination in trips:
            if origin == destination:
                pass
            else:
                srs.index = [c if (('Weapon' not in c) or (int(re.search(r'\d+', c).group()) != origin)) \
                                 else c.replace(re.search(r'\d+', c).group(), str(destination)) for c in srs.index]

        return srs

    # More cavorting...
    weapons = units.apply(weaponify, axis='columns')
    units = units.drop([c for c in units.columns if 'Weapon' in c], axis=1).join(weapons)
    hashes = pd.read_csv(parser.parse_args().path + "/" + parser.parse_args().version +
                        "/ZZ_Win/pc/localisation/us/localisation/unites_fixed.csv",
                         encoding='windows-1252',
                         index_col=0)

    # Clean, clean, clean, clean, clean
    decks = {
        '8BD43C9757360E00': 'Mechanized',
        '5C76718B57360E00': 'Armored',
        '5E767965E3000000': 'Motorized',
        'DAD77965E3000000': 'Support',
        '23B8605ED9380000': 'Marine',
        '0BB7685ED9380000': 'Airborne'
    }

    deck_types = units['UnitTypeTokens'].map(eval).map(lambda l: [decks[i] for i in l])
    units['MechanizedDeck'] = deck_types.map(lambda t: 'Mechanized' in t)
    units['ArmoredDeck'] = deck_types.map(lambda t: 'Armored' in t)
    units['MotorizedDeck'] = deck_types.map(lambda t: 'Motorized' in t)
    units['SupportDeck'] = deck_types.map(lambda t: 'Support' in t)
    units['MarineDeck'] = deck_types.map(lambda t: 'Marine' in t)
    units['AirborneDeck'] = deck_types.map(lambda t: 'Airborne' in t)

    movers = {
        1: 'Foot',
        2: 'Wheeled',
        3: 'Wheeled',
        5: 'Tracked',
        6: 'Air',
        7: 'Wheeled',
        8: 'Tracked',
        9: 'Water'
    }
    amphib = {
        1: False,
        2: False,
        3: False,
        5: False,
        6: np.nan,
        7: True,
        8: True,
        9: np.nan
    }

    units['MovementType'] = units['UnitMovingType'].map(movers)
    units['Amphibious'] = units['UnitMovingType'].map(amphib)

    training = {
        '8F37594F19619C07': 'Elite',
        '5593495D19619C07': 'Shock',
        'D6173D5C19619C07': 'Regular',
        'DE644D5719619C07': 'Militia',
        'null': np.nan
    }

    units['Training'] = units['Training'].map(training)

    ciws = {
        '4F233E0000000000': 'Exceptional',
        '4E96452000000000': 'Very Good',
        '4E96450000000000': 'Good',
        'D672711906000000': 'Medium',
        'CEC2000000000000': 'Bad',
        'null': np.nan
    }

    units['CIWS'] = units['CIWS'].map(ciws)

    sailing = {
        'CBD32D65B4780000': 'Deep Sea',
        'CBD33165B4780000': 'Coastal',
        'CBD33565B4780000': 'Riverine',
        'null': np.nan
    }
    units['Sailing'] = units['Sailing'].map(sailing)

    units['HitRollSizeModifier'] = units['HitRollSizeModifier'].map(lambda v: float(v) if v != "null" else np.nan)

    mother_country = {
        'US': 'United States',
        'UK': 'United Kingdom',
        'FR': 'France',
        'RFA': 'West Germany',
        'CAN': 'Canada',
        'SWE': 'Sweden',
        'NOR': 'Norway',
        'DAN': 'Denmark',
        'ANZ': 'ANZAC',
        'JAP': 'Japan',
        'ROK': 'South Korea',
        'ISR': 'Israel',
        'HOL': 'The Netherlands',
        'URSS': 'Soviet Union',
        'RDA': 'East Germany',
        'TCH': 'Czechoslavakia',
        'POL': 'Poland',
        'CHI': 'China',
        'NK': 'North Korea',
        'YUG': 'Yugoslavia',
        'FIN': 'Finland',
        'SA': 'South Africa'
    }

    units['MotherCountry'] = units['MotherCountry'].map(mother_country)
    units['ProductionYear'] = units['ProductionYear'].map(lambda v: int(v) if v != "null" else np.nan)
    units['MaxPacks'] = units['MaxPacks'].map(lambda v: int(v) if v != "null" else np.nan)

    tab = {
        3: 'LOG',
        6: 'INF',
        7: 'PLA',
        8: 'VHC',
        9: 'TNK',
        10: 'REC',
        11: 'HEL',
        12: 'SHP',
        13: 'SUP',
        "null": np.nan
    }
    units['Tab'] = units['Factory'].map(tab)

    units['ProductionPrice'] = units['ProductionPrice'].map(lambda l: eval(l)[0] if len(eval(l)) > 0 else np.nan)
    units['IsPrototype'] = units['IsPrototype'].map(lambda v: True if v == "True" else False)
    units['HitRollECMModifier'] = units['HitRollECMModifier'].map(lambda v: float(v) if v != "null" else np.nan)

    units['Maxspeed'] = units['Maxspeed'] / 52
    units['MaxSpeed'] = units['Maxspeed']
    del units['Maxspeed']

    units = units.rename(columns={'TempsDemiTour': 'TimeHalfTurn'})
    units = units.drop(['_ShortDatabaseName', 'StickToGround', 'ManageUnitOrientation',
                        'IconeType', 'PositionInMenu', 'NameInMenuToken', 'AliasName', 'Category',
                        'AcknowUnitType', 'TypeForAcknow', 'Factory',
                        'CoutEtoile', 'UnitTypeTokens', 'UnitMovingType', 'Key',
                        'TypeUnitValue', 'UnitInfoJaugeType',
                        'SpeedBonusOnRoad', 'VehicleSubType', 'TerrainsToIgnoreMask',
                        'DeploymentDuration', 'WithdrawalDuration',
                        ], axis='columns')

    deployables = units['MaxDeployableAmount'].map(lambda l: [int(v) for v in eval(l)])
    units['RookieDeployableAmount'] = [d[0] for d in deployables]
    units['TrainedDeployableAmount'] = [d[1] for d in deployables]
    units['HardenedDeployableAmount'] = [d[2] for d in deployables]
    units['VeteranDeployableAmount'] = [d[3] for d in deployables]
    units['EliteDeployableAmount'] = [d[4] for d in deployables]

    units['UnitStealthBonus'] = units['UnitStealthBonus'].map(lambda v: float(v) if v != "null" else np.nan)
    units['AutoOrientation'] = units['AutoOrientation'].map(lambda v: True if v != "null" else False)

    def splash(v):
        return True if 1 <= v <= 4 else False

    units['ArmorFrontSplashResistant'] = units['ArmorFront'].map(splash)
    units['ArmorSidesSplashResistant'] = units['ArmorSides'].map(splash)
    units['ArmorRearSplashResistant'] = units['ArmorRear'].map(splash)
    units['ArmorTopSplashResistant'] = units['ArmorTop'].map(splash)

    av = lambda v: v if v <= 4 else v - 4

    units['ArmorFront'] = units['ArmorFront'].map(av)
    units['ArmorSides'] = units['ArmorSides'].map(av)
    units['ArmorRear'] = units['ArmorRear'].map(av)
    units['ArmorTop'] = units['ArmorTop'].map(av)

    units['CanWinExperience'] = units['CanWinExperience'].map(lambda v: True if v != "null" else False)
    units['IsCommandUnit'] = units['IsCommandUnit'].map(lambda v: True if v != "null" else False)
    units['IsShip'] = units['IsTargetableAsBoat'].map(lambda v: True if v != "null" else False)
    units = units.drop(['IsTargetableAsBoat'], axis='columns')

    del units['CanWinExperience']
    del units['ExperienceGainBySecond']
    del units['GunMuzzleSpeed']
    del units['MaxDeployableAmount']
    del units['PaliersPhysicalDamages']
    del units['PaliersSuppressDamages']
    del units['ShowInMenu']
    del units['SuppressDamagesRegenRatioOutOfRange']
    del units['VitesseCombat']

    units['LowAltitudeFlyingAltitude'] = units['LowAltitudeFlyingAltitude'].map(
        lambda v: int(v) / 52 if v != "null" else np.nan)
    units['NearGroundFlyingAltitude'] = units['NearGroundFlyingAltitude'].map(
        lambda v: int(v) / 52 if v != "null" else np.nan)
    units = units.rename(columns={'LowAltitudeFlyingAltitude': 'HelicopterFlyingAltitude',
                                  'NearGroundFlyingAltitude': 'HelicopterHoverAltitude'})

    units['MinimalAltitude'] = units['MinimalAltitude'] / 52
    units = units.rename(columns={'MinimalAltitude': 'AirplaneMinimalAltitude'})
    units = units.rename(columns={'MaxDamages': 'Strength'})
    units = units.rename(columns={'MaxSuppressionDamages': 'SuppressionCeiling'})
    units['OpticalStrengthAntiradar'] = units['OpticalStrengthAntiradar'].map(
        lambda v: int(v) if v != "null" else np.nan)
    units['PorteeVisionTBA'] = units['PorteeVisionTBA'].map(lambda v: int(v) if v != "null" else np.nan)
    units = units.rename(columns={'ProductionPrice': 'Price'})
    units = units.rename(columns={'ProductionYear': 'Year'})
    units = units.rename(
        columns={'StunDamagesRegen': 'StunDamageRegen', 'StunDamagesToGetStunned': 'StunDamageToGetStunned'})
    units['IsTransporter'] = units['Transporter'].map(lambda v: True if v != "null" else False)
    del units['Transporter']
    units = units.rename(columns={'UnitStealthBonus': 'Stealth'})

    units = units.rename(columns={'UpgradeRequired': 'Upgrade'})
    def upgradify(srs):
        # print(srs['Upgrade'])
        if pd.isnull(srs['Upgrade']):
            return [srs['ID']]
        else:
            return [srs['ID']] + upgradify(units.query('ID == {0}'.format(srs['Upgrade'])).iloc[0])
    all_upgrade_paths = np.unique(units.apply(upgradify, axis='columns').values)
    all_upgrade_paths_sorted = sorted([sorted(l, reverse=False) for l in all_upgrade_paths], reverse=False)
    all_full_paths = []
    for i in range(len(all_upgrade_paths_sorted) - 1):
        if all_upgrade_paths_sorted[i] == []:
            pass
        else:
            flag = True
            for sublist in all_upgrade_paths_sorted[:i] + all_upgrade_paths_sorted[i + 1:]:
                if len(set(all_upgrade_paths_sorted[i]).intersection(set(sublist))) == len(
                        set(all_upgrade_paths_sorted[i])):
                    flag = False
                    break
            if flag:
                all_full_paths.append(all_upgrade_paths_sorted[i])
    upgrade_paths_lookup = dict()
    for l in all_full_paths:
        for e in l:
            upgrade_paths_lookup[e] = l

    import itertools

    def transporterify(srs):
        ret = srs.copy()
        ind = 0
        if isinstance(ret['Transporters'], str):
            transporters = [int(v) for v in eval(ret['Transporters'])]
            ret['Transporters'] = list(itertools.chain.from_iterable([upgrade_paths_lookup[v] for v in transporters]))
            for i in range(len(ret['Transporters'])):
                ret['Transporter{0}ID'.format(i + 1)] = ret['Transporters'][i]
        return ret

    units = units.apply(transporterify, axis='columns')

    def upgradesto(uid):
        try:
            upgrade_set = upgrade_paths_lookup[uid]
            for luid in [e for e in upgrade_set if e != uid]:
                if units.query("ID == {0}".format(luid)).iloc[0]['Upgrade'] == uid:
                    return luid
        except:
            pass

    units['UpgradeTo'] = units['ID'].apply(upgradesto)
    units = units.rename(columns={'Upgrade': 'UpgradeFrom'})

    del units['DeathExplosionArme']
    del units['DeathExplosionRadiusSplashPhysicalDamages']
    del units['DeathExplosionRadiusSplashSuppressDamages']
    del units['DeathExplosionSuppressDamages']
    del units['DeathExplosionID']

    units['DetectionTBA'] = units['DetectionTBA'].map(lambda v: v / 52)
    units = units.rename(columns={'DetectionTBA': 'HelicopterDetectionRadius'})
    units = units.rename(columns={'FuelMoveDuration': 'Autonomy'})
    units['FlyingAltitude'] = units['FlyingAltitude'] / 52
    units = units.rename(columns={'FlyingAltitude': 'AirplaneFlyingAltitude'})
    units['HelicopterFlyingAltitude'] = units['HelicopterFlyingAltitude'].map(lambda v: v if v == 150.0 else np.nan)
    units['MaxAcceleration'] = units['MaxAcceleration'] / 52
    units['MaxDeceleration'] = units['MaxAcceleration'] / 52
    del units['KillExperienceBonus']
    units = units.rename(columns={'OpticalStrength': 'OpticalStrengthGround'})
    units['PorteeVision'] = units['PorteeVision'] / 52
    units = units.rename(columns={'PoteeVision': 'GroundDetectionRadius'})
    units['PorteeVisionTBA'] = units['PorteeVisionTBA'] / 52
    units = units.rename(columns={'PorteeVisionTBA': 'AirToAirHelicopterDetectionRadius'})
    units['UpwardSpeed'] = units['UpwardSpeed'] / 52
    del units['Transporters']
    units = units.rename(columns={'OpticalStrengthAltitude': 'OpticalStrengthAir'})

    def recon(v):
        if "#reco1" in v:
            return "Good"
        elif "reco2" in v:
            return "Very Good"
        elif "reco3" in v:
            return "Exceptional"
        else:
            return np.nan
    units['Optics'] = units['NameInMenu'].map(recon)
    units['NameInMenu'] = units['NameInMenu'].map(lambda n: n.replace("#command ", "") \
                                                  .replace("#reco1", "") \
                                                  .replace("#reco2", "") \
                                                  .replace("#reco3", "") \
                                                  .strip())

    def hashquery(uhash):
        if pd.notnull(uhash):
            try:
                return hashes.query("Hash == '{0}'".format(uhash)).iloc[0]['String']
            except IndexError:
                print("WARNING: Hash {0} failed to match!".format(uhash))
                return np.nan
        else:
            return np.nan

    # for h in units['Weapon{0}Name'.format(1)]:
    #     try:
    #         a = hashquery(h)
    #         pass
    #     except IndexError:
    #         import pdb; pdb.set_trace()

    for i in range(1, 12):
        units['Weapon{0}Name'.format(i)] = units['Weapon{0}Name'.format(i)].map(hashquery)
        units['Weapon{0}TypeArme'.format(i)] = units['Weapon{0}TypeArme'.format(i)].map(hashquery)
        units['Weapon{0}Caliber'.format(i)] = units['Weapon{0}Caliber'.format(i)].map(hashquery)

    # Unfortunately our hash cut off the "," in 5,45mm rounds and 7,62mm rounds, both valid calibers. We can fix
    # this manually. And others.
    def fixmgcaliber(c):
        if str(c) == "7":
            return "7,62mm"
        elif str(c) == "5":
            return "5,45mm"
        elif str(c) == "12":
            return "12,7mm"
        elif str(c) == "14":
            return "14,5mm"
        elif str(c) == "4":
            return "4,73mm"
        elif str(c) == "6":
            return "6,5mm"
        elif str(c) == "7":
            return "72,5mm"
        else:
            return c

    for i in range(1, 12):
        units['Weapon{0}Caliber'.format(i)] = units['Weapon{0}Caliber'.format(i)].map(fixmgcaliber)

    def weaponify2(srs):
        ret = pd.Series()
        for wi in [i for i in range(1, 12) if pd.notnull(srs['Weapon{0}Name'.format(i)])]:
            fragment = "Weapon{0}".format(wi)
            ret[fragment + 'Tags'] = []
            arme = srs[fragment + 'Arme']
            arme = float(arme) if arme != "null" else np.nan
            type_arme = srs[fragment + 'TypeArme']
            physical = srs[fragment + 'PhysicalDamages']
            physical = float(physical) if physical != "null" else np.nan
            # Determine AP.
            if arme < 3 or arme == "null":
                ret[fragment + 'AP'] = np.nan
            elif arme == 3:
                if type_arme not in ['Rocket Launcher', 'HMG', 'MMG', 'Flamethrower'] and 'Bomb' not in type_arme:
                    ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['AoE']
                ret[fragment + 'AP'] = np.nan
            elif arme == 4:
                ret[fragment + 'AP'] = np.nan
            elif type_arme == "SSM":
                ret[fragment + 'AP'] = (arme - 34) * physical
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['HEAT']
            elif 5 <= arme <= 34:
                ret[fragment + 'AP'] = arme - 4
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['KE']
                if type_arme not in ['Rocket Launcher', 'HMG', 'MMG', 'Flamethrower'] and 'Bomb' not in type_arme:
                    ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['AoE']
            elif 35 <= arme <= 65:
                ret[fragment + 'AP'] = arme - 34
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['HEAT']
                if type_arme in ['Autocannon', 'Main Gun']:  # Thunderbolt, AMX-30, etc.
                    ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['AoE']

                    # Determine HE.
            if physical == "null":
                ret[fragment + 'HE'] = np.nan
            else:
                ret[fragment + 'HE'] = physical

            # Conversions
            for c in ['RadiusSplashPhysicalDamages', 'Puissance', 'TempsEntreDeuxTirs', 'TempsEntreDeuxSalves',
                      'NbrProjectilesSimultanes', 'NbTirParSalves', 'RadiusSplashSuppressDamages', 'TempsDeVisee',
                      'DispersionAtMaxRange', 'DispersionAtMinRange', 'CorrectedShotDispersionMultiplier']:
                if srs[fragment + c] == "null":
                    srs[fragment + c] = np.nan
                else:
                    srs[fragment + c] = float(srs[fragment + c])
            for c in [c for c in ['MissileMaxSpeed', 'MissileMaxAcceleration'] if fragment + c in srs.index]:
                if srs[fragment + c] == "null":
                    srs[fragment + c] = np.nan
                else:
                    srs[fragment + c] = float(srs[fragment + c])
                ret[fragment + c] = srs[fragment + c] / 52
                ret[fragment + c] = srs[fragment + c] / 52

            ret[fragment + 'RadiusSplashPhysicalDamage'] = srs[fragment + 'RadiusSplashPhysicalDamages'] * 175 / 13000
            ret[fragment + 'Noise'] = srs[fragment + 'Puissance']
            ret[fragment + 'TimeBetweenShots'] = srs[fragment + 'TempsEntreDeuxTirs']
            ret[fragment + 'TimeBetweenSalvos'] = srs[fragment + 'TempsEntreDeuxSalves']
            ret[fragment + 'ProjectilesPerShot'] = srs[fragment + 'NbrProjectilesSimultanes']
            ret[fragment + 'ShotsPerSalvo'] = srs[fragment + 'NbTirParSalves']
            ret[fragment + 'RadiusSplashSuppressDamage'] = srs[fragment + 'RadiusSplashSuppressDamages'] * 175 / 13000
            ret[fragment + 'AimTime'] = srs[fragment + 'TempsDeVisee']
            ret[fragment + 'DispersionAtMaxRange'] = srs[fragment + 'DispersionAtMaxRange'] * 175 / 13000
            ret[fragment + 'DispersionAtMinRange'] = srs[fragment + 'DispersionAtMinRange'] * 175 / 13000

            # Distance convesions
            for c in ['PorteeMaximale', 'PorteeMinimale', 'PorteeMinimaleBateaux', 'PorteeMaximaleBateaux',
                      'PorteeMaximaleTBA', 'PorteeMinimaleTBA', 'PorteeMinimaleHA', 'PorteeMaximaleHA',
                      'PorteeMaximaleProjectile', "PorteeMinimaleProjectile"]:
                if srs[fragment + c] == "null":
                    srs[fragment + c] = np.nan
                else:
                    srs[fragment + c] = float(srs[fragment + c])
            ret[fragment + 'RangeGround'] = srs[fragment + 'PorteeMaximale'] * 175 / 13000
            ret[fragment + 'RangeGroundMinimum'] = srs[fragment + 'PorteeMinimale'] * 175 / 13000
            ret[fragment + 'RangeShip'] = srs[fragment + 'PorteeMaximaleBateaux'] * 175 / 13000
            ret[fragment + 'RangeShipMinimum'] = srs[fragment + 'PorteeMinimaleBateaux'] * 175 / 13000
            ret[fragment + 'RangeHelicopters'] = srs[fragment + 'PorteeMaximaleTBA'] * 175 / 13000
            ret[fragment + 'RangeHelicoptersMinimum'] = srs[fragment + 'PorteeMinimaleTBA'] * 175 / 13000
            ret[fragment + 'RangePlanes'] = srs[fragment + 'PorteeMaximaleHA'] * 175 / 13000
            ret[fragment + 'RangePlanesMinimum'] = srs[fragment + 'PorteeMinimaleHA'] * 175 / 13000
            ret[fragment + 'RangeMissiles'] = srs[fragment + 'PorteeMaximaleProjectile'] * 175 / 13000
            ret[fragment + 'RangeMissilesMinimum'] = srs[fragment + 'PorteeMinimaleProjectile'] * 175 / 13000

            # Level
            lvl = srs[fragment + 'Level']
            if lvl == "null":
                ret[fragment + 'PositionOnCard'] = np.nan
            else:
                ret[fragment + 'PositionOnCard'] = int(lvl)

            # Guidance
            guid = srs[fragment + "Guidance"]
            if str(guid) == '1' and srs['Tab'] != "PLA":  # avoid tagging radar missiles on planes.
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['RAD']
            if str(guid) == '2':
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['SEAD']

            # Accuracies
            for c in ['HitProbability', 'HitProbabilityWhileMoving', 'MinimalCritProbability',
                      'MinimalHitProbability']:
                if srs[fragment + c] == "null":
                    ret[fragment + c] = np.nan
                else:
                    ret[fragment + c] = srs[fragment + c]
            if srs[fragment + 'TirEnMouvement'] == "null":
                srs[fragment + 'HitProbabilityWhileMoving'] = np.nan
                ret[fragment + 'HitProbabilityWhileMoving'] = np.nan

            # Rest of the tags.
            if type_arme == "SAW":
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['CQC']
            if pd.notnull(ret[fragment + 'RangeMissiles']):
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['DEF']
            if srs[fragment + 'TirIndirect'] != "null" and "Bomb" not in srs[fragment + 'TypeArme']:
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['CORR']
            if srs[fragment + 'IsFireAndForget'] != "null":
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['F&F']
            if srs[fragment + 'IgnoreInflammabilityConditions'] != "null":
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['NPLM']
            if srs[fragment + 'IsSubAmmunition'] != "null":
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['CLUS']
            if pd.isnull(ret[fragment + 'RangeGround']) and pd.notnull(ret[fragment + 'RangeShip']) \
                    and ret[fragment + 'RangeShip'] > 0:
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['SHIP']
            # import pdb; pdb.set_trace()
            if pd.isnull(srs[fragment + 'HitProbabilityWhileMoving']) and srs[fragment + 'IsFireAndForget'] == "null" \
                    and pd.notnull(srs[fragment + 'MissileMaxSpeed']):
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['GUID']
            elif pd.isnull(srs[fragment + 'HitProbabilityWhileMoving']):
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['STAT']
            if srs[fragment + 'TirEnMouvement'] == "True" and srs[fragment + 'IsFireAndForget'] == "null" \
                    and pd.notnull(srs[fragment + 'MissileMaxSpeed']):
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['SA']
            if fragment + 'CanSmoke' in srs.index and srs[fragment + 'CanSmoke'] == True:
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['SMK']

            # AoE corrections.
            # AoE, it turns out, can only be read off of a unit by checking whether or not the HE component of the weapon
            # has an Arme of 3. I

            # TODO: Smoke
            # I attached smoke incorrect, it gets associated with the weapon one after the one that actually does smoke.
            # Because I attached CanSmoke incorrectly this will have to be done using a far more tedious process.
            # It will

            # Classifiers.
            ret[fragment + 'Name'] = srs[fragment + 'Name']
            ret[fragment + 'Type'] = srs[fragment + 'TypeArme']
            ret[fragment + 'Caliber'] = srs[fragment + 'Caliber']

            salvo_num = srs[fragment + 'SalvoStockIndex']
            salvo_num = int(float(salvo_num)) if salvo_num != "null" else 0
            number_shots_per_salvo = eval(srs['Salves'])[salvo_num]
            ret[fragment + 'NumberOfSalvos'] = int(number_shots_per_salvo)
            ret[fragment + 'DisplayedAmmunition'] = srs[fragment + 'AffichageMunitionParSalve'] * ret[
                fragment + 'NumberOfSalvos']

            # Hidden tags.
            if srs[fragment + 'TirIndirect'] != "null" and ret[fragment + 'AimTime'] == 10:
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['IFC']
            if ret[fragment + 'NumberOfSalvos'] == 1 and type_arme == "Main Gun":
                ret[fragment + 'Tags'] = ret[fragment + 'Tags'] + ['AL']

            # Direct carry-overs:
            for field in ["AngleDispersion", "RayonPinned", "FireTriggeringProbability", "SupplyCost",
                          "MissileTimeBetweenCorrections", "CorrectedShotDispersionMultiplier"]:
                ret[fragment + field] = srs[fragment + field] if srs[fragment + field] != "null" else np.nan
            ret[fragment + 'CanSmoke'] = True if fragment + 'CanSmoke' in srs.index else False
        return ret

    weaponified = units.apply(weaponify2, axis='columns')
    units_weaponified = units[[c for c in units.columns if 'Weapon' not in c]].join(weaponified)

    for i in range(1, 12):
        units_weaponified['Weapon{0}Tags'.format(i)] = units_weaponified['Weapon{0}Tags'.format(i)] \
            .map(lambda l: "|".join(l) if isinstance(l, list) else np.nan)

    def merge_transporters(srs):
        uidl = [srs['Transporter{0}ID'.format(i)] for i in range(1, 14)]
        uidl = [str(int(uid)) for uid in uidl if pd.notnull(uid)]
        return "|".join(uidl)
    units_weaponified['Transporters'] = units_weaponified.apply(merge_transporters, axis='columns')
    for i in range(1, 14):
        del units_weaponified['Transporter{0}ID'.format(i)]

    def merge_deck_types(srs):
        types = []
        for deck in ['Mechanized', 'Motorized', 'Marine', 'Airborne', 'Armored', 'Support']:
            if srs[deck + 'Deck'] == True:
                types.append(deck)
        return "|".join(types)
    units_weaponified['Decks'] = units_weaponified.apply(merge_deck_types, axis='columns')

    units_weaponified = units_weaponified.rename(columns={
        'NameInMenu': 'Name',
        'HitRollECMModifier': 'ECM',
        'HitRollSizeModifier': 'SizeModifier',
        'HitProbability': 'Accuracy',
        'HitProbabilityWhileMoving': 'Stabilizer',
        'MinimalHitProbability': 'MinimalAccuracy',
    })

    for deck in ['Mechanized', 'Motorized', 'Marine', 'Airborne', 'Armored', 'Support']:
        del units_weaponified[deck + 'Deck']

    units_weaponified.to_csv("../data/"  + parser.parse_args().version + "/final_data.csv", encoding='utf-8')


if __name__ == "__main__":
    main()
