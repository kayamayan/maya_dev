@set YEAR=%date:~0,4%
@set MONTH=%date:~5,2%
@set DAY=%date:~8,2%

@set DAYSTRING=%YEAR%%MONTH%%DAY%

mkdir Z:\9_Daily\%DAYSTRING%
mkdir "C:\Users\cine-render\OneDrive - Madngine\Daily\%DAYSTRING%"
xcopy Z:\9_Daily\_PERSISTENT\*.* Z:\9_Daily\%DAYSTRING% /y >> "D:\dailyrender\persistent_%DAYSTRING%.log"
xcopy "C:\Users\cine-render\OneDrive - Madngine\Daily\_PERSISTENT\*.*" "C:\Users\cine-render\OneDrive - Madngine\Daily\%DAYSTRING%" /y >> "D:\dailyrender\persistent_%DAYSTRING%.log"

"C:\Users\cine-render\AppData\Local\Programs\Python\Python311\python.exe" D:\dailyrender\DailyRender_v2.py >> "D:\dailyrender\render_%DAYSTRING%.log"

