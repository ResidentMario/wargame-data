import argparse
import subprocess
from tqdm import tqdm
import os

parser = argparse.ArgumentParser(description="""
A command-line utility that automates exporting Wargame: Red Dragon internal XML files.
""")
parser.add_argument("exporter", help="A filepath to your copy of the WGTableExporter utility. (e.g. "
                                     "C:/Users/WargamerGuy/Desktop/tableexporter/WGTableExporter.exe)")
parser.add_argument("wargame", help="A filepath to the folder containing top-level Wargame: Red Dragon data files ("
                                    "e.g. C:\Steam\steamapps\common\Wargame Red Dragon\Data\WARGAME\PC).")
parser.add_argument("version", default="Everything", help="The patch version of the game (e.g. 430000626) to export "
                                                          "the data from. By default, export everything.",
                    nargs='?')

# Pull the tables. This is a lengthy process, but relatively straightforward: execute the proper WGTableExporter on
# each of the tables in interest in the given Wargame version.
# TODO: There will likely be more tables of interest.
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
subprocess.run(["move", "NDF_Win", "../raws/{0}".format(parser.parse_args().version)], shell=True)

# Pull the units dictionary.
# To do so we first have to find the most recent ZZ_Win.dat file. ZZ_Win.dat is the file which contains many of the
# localization dictionaries used by the game, but for reasons unknown to me it never appears in the most recent
# version of the game, only in previous versions.
#
# When it appears at all, it is located in a subdirectory of the root file which is another copy of the patch name
# (e.g. C:\Steam\steamapps\common\Wargame Red Dragon\Data\WARGAME\PC\510049986\510053208). So it takes some work to
# get to it.
#
# But wait! There's more! That particualr copy of ZZ_Win.dat might not even contain the localization subinformation
# at all! We can check this by running the exporter and then checking if we actually created a unites.dic; if yes
# break, if no keep backtracking.
#
# What a pain.
folders = os.listdir(parser.parse_args().wargame.replace("\\", "/"))
i = folders.index(parser.parse_args().version)
while True:
    previous_version = folders[i - 1]
    version = folders[i]
    if version in os.listdir(
        '{0}/{1}'.format(parser.parse_args().wargame, previous_version).replace("\\", "/")
    ):
        zz_win = '{0}/{1}/{2}/ZZ_Win.dat'.format(parser.parse_args().wargame,
                                                 previous_version,
                                                 version).replace("\\", "/")
        comm = ['{0}'.format(parser.parse_args().exporter), zz_win, r"pc\localisation\us\localisation\unites.dic"]
        subprocess.run(comm, shell=True)
        import pdb; pdb.set_trace()
        if "ZZ_Win" in os.listdir("."):
            break
        else:
            i -= 1
    else:
        i -= 1
subprocess.run(["move", "ZZ_Win", "../raws/{0}".format(parser.parse_args().version)], shell=True)