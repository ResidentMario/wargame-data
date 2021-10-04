import argparse

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description="""
Parse an intermediate Wargame: Red Dragon data file into a finished product.
""")
parser.add_argument("path", help="A filepath to the folder containing XML dumps to be processed (e.g. "
                                 "C:\\Users\\Alex\\Desktop\\wargame-analysis\\raws).")
parser.add_argument("version", help="The version of Wargame: Red Dragon to be processed (e.g. 510049986). Should be a "
                                    "subfolder of the filepath above.")
parser.add_argument("wargame", help="Pass")
parser.add_argument('--combine', dest='combine',  action='store_true', help="add FOB buildings to final_data.csv")

fobs = pd.read_csv(parser.parse_args().wargame + "/" + parser.parse_args().version + "/raw_fobs.csv",
                   index_col=0)

tab = {
    3: 'LOG',
    6: 'INF',
    7: 'PLA',
    8: 'VHC',
    9: 'TNK',
    10: 'REC',
    11: 'HEL',
    12: 'SHP',
    13: 'SUP'
}
fobs['Tab'] = fobs['Factory'].map(tab).fillna(np.nan)

decks = {
    '8BD43C9757360E00': 'Mechanized',
    '5C76718B57360E00': 'Armored',
    '5E767965E3000000': 'Motorized',
    'DAD77965E3000000': 'Support',
    '23B8605ED9380000': 'Marine',
    '0BB7685ED9380000': 'Airborne'
}

deck_types = fobs['UnitTypeTokens'].map(eval).map(lambda l: [decks[i] for i in l])
fobs['MechanizedDeck'] = deck_types.map(lambda t: 'Mechanized' in t)
fobs['ArmoredDeck'] = deck_types.map(lambda t: 'Armored' in t)
fobs['MotorizedDeck'] = deck_types.map(lambda t: 'Motorized' in t)
fobs['SupportDeck'] = deck_types.map(lambda t: 'Support' in t)
fobs['MarineDeck'] = deck_types.map(lambda t: 'Marine' in t)
fobs['AirborneDeck'] = deck_types.map(lambda t: 'Airborne' in t)


def merge_deck_types(srs):
    types = []
    for deck in ['Mechanized', 'Motorized', 'Marine', 'Airborne', 'Armored', 'Support']:
        if srs[deck + 'Deck']:
            types.append(deck)
    return "|".join(types)


fobs['Decks'] = fobs.apply(merge_deck_types, axis='columns')

deployables = fobs['MaxDeployableAmount'].map(lambda l: [int(v) for v in eval(l)])
fobs['RookieDeployableAmount'] = [d[0] for d in deployables]
fobs['TrainedDeployableAmount'] = [d[1] for d in deployables]
fobs['HardenedDeployableAmount'] = [d[2] for d in deployables]
fobs['VeteranDeployableAmount'] = [d[3] for d in deployables]
fobs['EliteDeployableAmount'] = [d[4] for d in deployables]

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
    'FIN': 'Finland'
}

fobs['MotherCountry'] = fobs['MotherCountry'].map(mother_country)

fobs['ProductionPrice'] = fobs['ProductionPrice'].map(lambda l: eval(l)[0] if len(eval(l)) > 0 else np.nan)
fobs = fobs.rename(columns={'ProductionPrice': 'Price'})

fobs = fobs.drop(["_ShortDatabaseName", "Category", "Factory", "UnitTypeTokens", "NameInMenuToken",
                  "MaxDeployableAmount"], axis='columns')
fobs = fobs.rename(columns={"NameInMenu": "Name"})

if parser.parse_args().combine:
    data = pd.read_csv(parser.parse_args().wargame + "/" + parser.parse_args().version + "/final_data.csv",
                       index_col=0)
    data = data.append(fobs)
    data.reset_index(inplace=True, drop=True)
    data.to_csv("../data/" + parser.parse_args().version + "/final_data.csv", encoding='utf-8')
else:
    fobs.reset_index(inplace=True, drop=True)
    del fobs["ID"]
    fobs.to_csv("../data/" + parser.parse_args().version + "/final_fobs.csv", encoding='utf-8')

# TODO: SupplyCapacity	SupplyPriority
