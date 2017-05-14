@echo off

:: For tableexporter, make sure your to set your locale's decimal setting
:: to . instead of , if you have a non US region setting, otherwise clean.py
:: won't convert float characters correctly. This can be done in:
:: Start / Run / intl.cpl / Additional Settings / Numbers
SET tableexporter=%USERPROFILE%\Documents\src\table-exporter\WGTableExporter.exe

SET wargamedata=%USERPROFILE%\PycharmProjects\wargame-data
SET wargamesteam="D:\Steam\steamapps\common\Wargame Red Dragon\Data\WARGAME\PC"
SET rawsdir=%wargamedata%\raws
SET datadir=%wargamedata%\data

:: SET versions=(510053208 510064564)
SET versions=(510064564)

FOR %%I IN %versions% DO (
    REM Use /Q for interactive mode
    rmdir /S %rawsdir%\%%I
    rmdir /S %datadir%\%%I

    dump.py %tableexporter% %wargamesteam% %%I
    export.py --fobs %rawsdir%  %%I %datadir%
    clean.py %rawsdir% %%I  %datadir%
    fobs.py %rawsdir% %%I %datadir%

)

pause
