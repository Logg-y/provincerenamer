# ProvinceRenamer

This is a little program to randomly rename provinces on Dominions 5 .map files, intended for selecting just a few provinces to change to inside jokes and references of your choosing. Running the executable should be fairly self explanatory, but for completeness:

* renamechance: the chance to try renaming any given province (default 0.03 = 3%)
* mindistance: minimum distance between two renamed provinces to avoid clustering (default 3)
* map: the .map file to run on
* namelist: the namelist to draw names from

Once completed it spits out the map in the same folder with a _edited suffix.

## Namelist

This namelist files expect the following format:

Provname[tab]flaglist

Provname is the name of the province
Flaglist should be flags separated by tabs. The flags allowed are as follows:

Terrain flags - Provinces much match ALL of these to be valid
The exception is plains, which I think matches anything

* plains
* sea
* freshwater
* highlands OR gorge
* swamp
* forest OR kelpforest
* farm
* deepsea
* cave
* mountains

Terrain modifiers - if any are specified, only one must match to be valid

* small
* large
* nostart
* manysites
* throne
* start
* nothrone
* warmer
* colder

Special modifiers:

* inland - province has no connections to sea or deep sea provinces. Always enforced in addition to other modifiers

Included is a simple sample namelist.
