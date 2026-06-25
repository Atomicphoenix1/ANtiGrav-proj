@echo off
title Parse.bat

echo.
echo This batch file looks up and writes
echo information for the selected molecule.
echo.

pause

@echo off
REM %1 = input file.log
REM %2 = output file.txt

echo ---------- >  %2
echo ROUTE CARDS >> %2
echo Displays basis set and methods >> %2
find "# " %1 >> %2

echo ---------- >> %2
echo JOB CPU TIME >> %2
find "Job cpu time:" %1 >> %2

echo ---------- >> %2
echo SCF Done >> %2
find "SCF Done:" %1 >> %2

echo ---------- >> %2
find "Frequencies --" %1 >> %2
find "Raman Activ" %1 >> %2
find "IR Inten" %1 >> %2

more %2
