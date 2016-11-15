## Introduction

[Wargame: Red Dragon](https://en.wikipedia.org/wiki/Wargame:_Red_Dragon) is a real-time strategy video game which
simulates military encounters between democratic NATO (BLUFOR) and communist PACT (REDFOR) forces during the Cold War
. It is the third game in the series, published by the French company Eugen Entertainment; this particular iteration
is set in Asia, and introduced an Asian setting, Asian coalition members, and naval warfare to the game.

One of the game's draws is its fine-grained level of combat simulation. Players build "decks" composed of unit
"cards" to compete against one another with, and these cards provide a good at-a-glance overview of the complex and
combat simulation level the game's assets operate at:

![stuff](figures/T80UK-Unit-Card.png)

Although the statistics on these cards are a good first-order approximation, there is a whole second cadre of
gameplay mechanics and characteristics that these cards don't provide information on, as well as a number of
inaccuracies in presentation.

There are over 1700 units like this one, and balancing real time strategy games is hard. I (and others) are interested
in examining interactions between different units in the game. To that effect, this project aims to provide a
reproducible export of the "true" Wargame: Red Dragon (henceforth RD) unit values for the purposes of examination.

## Getting the Data


Each subfolder of `/data` contains a `final_data.csv`, the `CSV` dataset export, organized. **This file is of primary
 interest**. The datasets are organized by game version. Each game version corresponds with a patch to the game, and
 the higher the patch number the more recent the game version (right up to the current one). A patch log history is
 [available in the forums](http://forums.eugensystems.com/viewtopic.php?f=155&t=57546).

<!--

Each folder also contains a `raw_data.csv` file, which contains everything you need. However, note that since this
dataset is an uncompressed word-for-word copy of the game's gut internals, this dataset is *extremely*
verbose. It will only make sense if you have a deep understanding of the game's internals. A data dictionary is
provided in the form of the [Wargame Internal Values Manual](https://github.com/ResidentMario/wargame/blob/master/Wargame_Internal_Values_Manual.pdf).

-->


## Data Dictionary

* **ID** &mdash; The unit's unique ID.
* **NameInMenu** &mdash; The unit's name in-game.

#### Defense

* **ArmorFront**
* **ArmorSides**
* **ArmorTop**
* **ArmorRear**
* **ArmorFrontSplashResistant**
* **ArmorSidesSplashResistant**
* **ArmorTopSplashResistant**
* **ArmorRearSplashResistant** &mdash; Whether or not the unit is splash damage resistant on this side. Units which have
this property set to True and receive HE splash damage from the given direction (from, say, a bomb landing nearby)
will resist that damage as though they are fully armored, greatly reducing the damage they take compared to units
lacking both heavy armor and this property.
* **CIWS** &mdash; The CIWS level displayed on the unit card. Only non-null for ships. This variable is for
visual display only.
* **HitRollECMModifier** &mdash; A signed float of how much ECM the unit has.
* **HitRollSizeModifier** &mdash; A signed float of how the unit's size affects its chance to be hit.
* **Strength**
* **StunDamageRegen**
* **StunDamageToGetStunned** &mdash; Presumably, how much suppression damage the unit must receive (over an unknown
period of time) to get stunned. This variable and the one above are poorly understood.
* **SuppressDamageRatioIfTransporterKilled &mdash; What percentage of the unit's total suppression ceiling the
unit will take in suppression damage if the transporter it is in is destroyed and the unit survives.
* **SuppressionCeiling &mdash; Usually 800.

#### Card Data

* **Decks** &mdash; A pipe (`|`) delimited list of deck archetypes this unit appears in (e.g. `Airborne|Motorized|Marine`).
* **IsCommandUnit**
* **IsPrototype**
* **IsShip**
* **IsTransporter** &mdash; Whether or not this unit can transport other units (infantry if it is a ground carrier,
anything if it is a barge).
* **RookieDeployableAmount**
* **TrainedDeployableAmount**
* **HardenedDeployableAmount**
* **VeteranDeployableAmount**
* **EliteDeployableAmount**
* **MaxPacks** &mdash; The maximum number of cards of this unit which may be put into a deck.
* **MotherCountry**
* **Price**
* **ProductionTime** &mdash; How long, in seconds, it takes for the unit to appear.
* **Sailing** &mdash; Deep Sea, Coastal, or Riverine. Applies only to ships.
* **Tab**
* **Training** &mdash; Note that this variable, present only on infantry, is entirely cosmetic.
* **Transporters** &mdash; A pipe (`|`) delimited list of IDs of transporters for this unit (e.g. `15533|15534|16104`).
* **UpgradeFrom** &mdash; If this unit is an upgrade to (appears right of in the Armory to) another unit, the ID of that
other unit.
* **UpgradeTo** &mdash; If this unit upgrades to (appears left of in the Armory to) another unit, the ID of that other unit.
* **Year**

#### Weapons

Units in Wargame: Red Dragon may have up to 11 weapons mounted on-board (yes&mdash;far more than the three reported
on the card). This is due to naval units, which have many more weapons than those immediately displayed. The dataset
splits weapon characteristics into fields of the form `Weapon<N><ATTRIBUTE>`. So for example, the AP of the second
weapon on a unit would be reported by `Weapon2AP`. Following this schematic:

##### Identifying Characteristics
* **Name** &mdash; The weapon name (e.g. `M2 Browning`).
* **Type** &mdash; The weapon type (e.g. `Quad Autocannon`).
* **Caliber** &mdash; The displayed weapon caliber (e.g. `9mm Parabellum`).
* **DisplayedAmmunition** &mdash; The number of rounds of ammunition for a weapon is reproduced faithfully for large
weapons but incorrectly for small arms, which are simulated with up to one tenth as many in-game "bullets" as appear on
the card. This parameter is of the number of rounds shown on the card; for the actual number of rounds, refer to
`ShotsPerSalvo` and `NumberOfSalvos`.
* **PositionOnCard** &mdash; If this weapon is shown on the unit card, which of the three slots it falls into.
* **Tags** &mdash; A pipe (`|`) delimited list list of tags that apply to this weapon (e.g. `HEAT|STAT|F&F|`). For a
list of tags refer to [this wiki page](http://wargame-series.wikia.com/wiki/Weapons). Two hidden tags included in
this listing are autoloaders (`AL`) and integrated firing control (`IFC`).

##### Damage Output
* **AP**
* **HE**
* **RadiusSplashPhysicalDamage**
* **RadiusSplashSuppressDamage**

##### Aim/Shoot/Reload
* **AimTime**
* **ProjectilesPerShot**
* **TimeBetweenShots**
* **ShotsPerSalvo**
* **TimeBetweenSalvos**
* **NumberOfSalvos**

##### Accuracy
* **HitProbability**
* **HitProbabilityWhileMoving**
* **MinimalCritProbability**
* **MinimalHitProbability**
* **MissileTimeBetweenCorrections** &mdash; If the unit fires a missile, this is how many seconds between accuracy
"rerolls" on that shot. Rerolls are a strong accuracy debuff on slow-moving missiles.

##### Range
* **RangeGround**
* **RangeGroundMinimum**
* **RangeHelicopters**
* **RangeHelicoptersMinimum**
* **RangeMissiles**
* **RangeMissilesMinimum**
* **RangePlanes**
* **RangePlanesMinimum**
* **RangeShip**
* **RangeShipMinimum**

##### Dispersion
* **AngleDispersion**
* **DispersionAtMinRange**
* **DispersionAtMaxRange**
* **CorrectedShotDispersionMultiplier**

##### Misc
* **SupplyCost**
* **FireTriggeringProbability** &mdash; The probability that the impact of a unit of this weapon's round will start a
 fire. All napalm weapons have this parameter set to to 1, for example.
* **Noise** &mdash; How much noise this weapon generates when it is fired. Weapon firing noise usually makes a unit far
easier to spot, unless the weapon is silenced.
* **RayonPinned** &mdash; What this parameter does is unknown.


#### Movement

* **Amphibious** &mdash; Set to True if the unit can traverse water and False if it cannot traverse water. This field is
left empty if the unit is an air unit.
* **FuelCapacity** &mdash; How many liters of fuel the unit carries onboard, and, thereof, how expensive it is to refuel.
* **Autonomy** &mdash; How many seconds of movement a unit gets before it runs out of fuel.
* **MaxAcceleration**
* **MaxDeceleration**
* **MaxSpeed** &mdash; How fast the unit moves at full speed, in kilometers per hour. For planes, this is their flight
speed, as planes always move at the same speed.
* **MovementType** &mdash; Tracked, Wheeled, Foot, or Air.
* **TimeHalfTurn**

The following variables apply only to planes:

* **AirplaneFlyingAltitude** &mdash; Airplanes fly at this altitude.
* **AirplaneMinimalAltitude** &mdash; Airplanes refuse to go below this altitude (this was implemented in order to
deal with e.g. early "bugs" wherein a unit could accidentally bomb itself).

The following variables apply only to helicopters:

* **HelicopterFlyingAltitude**
* **HelicopterHoverAltitude**
* **CyclicManoeuvrability**
* **GFactorLimit**
* **LateralSpeed**
* **Mass**
* **MaxInclination**
* **RotorArea**
* **TorqueManoeuvrability**
* **UpwardsSpeed**

#### Vision

Not much is known about the mechanics of vision. Aside from distance normalization these values are reported as-is.

* **AirToAirHelicopterDetectionRadius** &mdash; Meter radius for air unit detection, used by air units.
* **HelicopterDetectionRadius** &mdash; Meter radius for helicopter detection.
* **IdentifyBaseProbability** &mdash; Unknown.
* **Optics** &mdash; If populated, one of Good, Very Good, or Exceptional.
* **OpticalStrengthAir** &mdash; Meter radius for air detection used by ground units.
* **OpticalStrengthAntiradar** &mdash; Meter radius for SEAD detection.
* **OpticalStrengthGround**  &mdash; Meter radius for ground detection.
* **Stealth** &mdash; The unit's stealth visibility multiplier. Note that this is *not* the Stealth value displayed
in-game, this is the actual in-engine multiplier.
* **TimeBetweenEachIdentifyRoll** &mdash; Unknown.

<!-- TODO: Delete PorteeVision, Salves, CanSmoke -->

#### Supply
* **SupplyCapacity**
* **SupplyPriority** &mdash; The lower the number, the greater the number of other supply units which will draw from this
 one.

#### Misc

* **AutoOrientation** &mdash; Whether or not the unit can be oriented using Ctrl+Drag. This is set to True for all
non-infantry units.
* **ClassNameForDebug** &mdash; The name the unit goes under within the internal game files. Not always entirely serious.

For further exposition on the data, refer to the [Wargame Internal Values Manual](https://github.com/ResidentMario/wargame/blob/master/Wargame_Internal_Values_Manual.pdf).

## Build Process
### Overview

RD has an [active modding community](http://forums.eugensystems.com/viewforum.php?f=187) (as did its predecessor in
the series, AirLand Battle). This community has produced a number of tools to aid them in their work.

The most important of these is the [Wargame Modding Suite](http://forums.eugensystems.com/viewtopic.php?t=45922), which
provides a centralized way of accessing, decompiling, and making changes to the game's binary files. This tool has
its own [GitHub repository](https://github.com/enohka/moddingSuite); a (potentially outdated) copy of its
documentation is saved [here](figures\wargame-modding-suite.pdf), for the purposes of posterity.

A second-order tool, built on top of this bedrock one, is the [Data Exporter](http://forums.eugensystems.com/viewtopic.php?f=187&t=57927&sid=3be76da66f1adb0d5a78b97d9f2f0d94).
This tool packages the Modding Suite into a command line tool for extracting specific tables from the game files.

This would be enough in and of itself, but the information we're interested in isn't exposed in top-level tables;
it's instead packed into a descending chain of containers, called "modules".

So to get a good, clean, well-formatted dataset, we need to export all of these tables, remap them to one another
out-of-binary, and then stitch their variables together.

### Step 1: Export the Raw Data

To export the raw data for a version of choice of Wargame: Red Dragon, first download Power Crystal's
[XML Data Exporter](http://forums.eugensystems.com/viewtopic.php?f=187&t=57927&hilit=XML+Exporter). Make sure you
have [Python 3.5](https://www.python.org/downloads/release/python-350/) or later installed, and that the copy of the
Wargame Modding Suite that comes with the data exporter is properly configured.

Either [clone this repository](https://git-scm.com/docs/git-clone) or copy and save
[`dump.py`](https://github.com/ResidentMario/wargame-data/blob/master/scripts/dump.py) somewhere
convenient. Open `Command Prompt` and navigate there. Then, run the following command:

    python export.py UTILITY VERSION OUTPUT

Replace `UTILITY` with the path to your copy of the Data Exporter's `WGTableExporter.exe` (e.g.
`C:/Users/WargamerGuy/Desktop/tableexporter/WGTableExporter.exe`).

Replace `VERSION` with the (numbered) version of the game whose data you want to export (e.g. `510049986`). The list
of all versions of the game you have locally should be located in your Steam files, e.g.
`E:\Steam\steamapps\common\Wargame Red Dragon\Data\WARGAME\PC`). The higher the number, the more recent the version,
right up to the current one.

Replace `OUTPUT` with the path of a folder that you want to write the data to (e.g. to save it to `Desktop` you would
 need something along the lines of `C:\Users\WargamerGuy\Desktop`).

What this will do: if you do all of this successfully, after a minute or two extracting the files you should have a
folder named for the version of the game you exported containing XML and CSV files constituting the game's unit data.

### Step 2: Datasetification

The raw XML output (clumsily) preserves all of the structure of the game's internal data. In order to make that
useful we have to flatten it&mdash;what I am here calling "Datasetification".

To do this you need to run the
[`export.py`](https://github.com/ResidentMario/wargame-data/blob/master/scripts/export.py) script. As before, run:

    python dump.py PATH VERSION OUTPUT

This time replace `PATH` to the folder containing the XML dumps you generated earlier, `VERSION` with the game
version, and `OUTPUT` with, once again, the folder you want to save the result to.

What this will do: after several minutes' processing time the folder you indicated should now contain a `CSV` file, e.g.
`510049986/raw_data.csv`. This file contains the game's unit data, flattened into a convenient format. Rejoice!

### Step 3: Simplification

Still to come.