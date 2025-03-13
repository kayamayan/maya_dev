@set YEAR=%date:~0,4%
@set MONTH=%date:~5,2%
@set DAY=%date:~8,2%

@set DAYSTRING=%YEAR%%MONTH%%DAY%

mkdir Z:\9_Daily\%DAYSTRING%
xcopy Z:\9_Daily\_PERSISTENT\*.* Z:\9_Daily\%DAYSTRING% /y >> "C:\DailyRender\persistent_%DAYSTRING%.log"

"python.exe" F:\gitRepos\daily_render\DailyRender_v2.py >> "C:\DailyRender\render_%DAYSTRING%.log"

