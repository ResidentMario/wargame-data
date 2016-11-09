import argparse
import subprocess
from tqdm import tqdm

parser = argparse.ArgumentParser(description="""
A command-line utility that automates exporting Wargame: Red Dragon internal XML files.
""")
parser.add_argument("exporter", help="A filepath to your copy of the WGTableExporter utility. (e.g. "
                                     "C:/Users/WargamerGuy/Desktop/tableexporter)")
parser.add_argument("wargame", help="A filepath to the folder containing top-level Wargame: Red Dragon data files ("
                                    "e.g. C:\Steam\steamapps\common\Wargame Red Dragon\Data\WARGAME\PC).")
parser.add_argument("version", default="Everything", help="The patch version of the game (e.g. 430000626) to export "
                                                          "the data from. By default, export everything.",
                    nargs='?')

for table in tqdm(["TAmmunition", "TMountedWeaponDescriptor", "TTurretUnitDescriptor", "TTurretTwoAxisDescriptor",
              "TTurretInfanterieDescriptor", "TTurretBombardierDescriptor", "TWeaponManagerModuleDescriptor",
              "TModuleSelector", "TFuelModuleDescriptor", "TMouvementHandlerLandVehicleDescriptor",
              "TMouvementHandlerHelicopterDescriptor", "TMouvementHandlerAirplaneDescriptor",
              "TModernWarfareDamageModuleDescriptor", "VisibilityModuleDescriptor",
              "TModernWarfareExperienceModuleDescriptor", "TModernWarfareCommmonDamageDescriptor",
              "TBlindageProperties", "TArmorDescriptor", "TUniteDescriptor",
              "TMouvementHandler_GuidedMissileDescriptor", "TScannerConfigurationDescriptor"]):
    comm = [
        '{0}'.format(parser.parse_args().exporter),
        '{0}/{1}/NDF_Win.dat'.format(parser.parse_args().wargame, parser.parse_args().version).replace("\\", "/"),
        r'pc\ndf\patchable\gfx\everything.ndfbin',
        '{0}'.format(table)
    ]
    subprocess.run(comm, shell=True)
import pdb; pdb.set_trace()
subprocess.run(["move", "NDF_Win", "../data/{0}".format(parser.parse_args().version)], shell=True)
# TODO: Export ZZ_Win.dat?