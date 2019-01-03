:again
FOR /F "tokens=*" %%g IN ('magick convert %1  -crop 1x1+1+1  txt:-') do (SET VAR=%%g)
for /F "tokens=3 delims= " %%a in ("%VAR%") do (
   SET VAR=%%a
)
echo:%VAR%
magick convert %1 -fuzz 40%% -fill none -opaque %VAR% %1
shift
if “%~1” == “” goto:eof
goto:again
pause