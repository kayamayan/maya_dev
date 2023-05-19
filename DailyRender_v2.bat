@set YEAR=%date:~0,4%
@set MONTH=%date:~5,2%
@set DAY=%date:~8,2%

@set DAYSTRING=%YEAR%%MONTH%%DAY%

mkdir T:\9_Daily\%DAYSTRING%
xcopy T:\9_Daily\_PERSISTENT\*.* T:\9_Daily\%DAYSTRING% /y >> "C:\DailyRender\persistent_%DAYSTRING%.log"

"C:\Program Files\Python37\python.exe" C:\DailyRender\DailyRender_v2.py >> "C:\DailyRender\render_%DAYSTRING%.log"

