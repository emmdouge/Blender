magick convert %1  -crop 1x1+1+1  txt:- 
FOR /F "tokens=*" %%g IN ('magick convert %1  -crop 1x1+1+1  txt:-') do (SET VAR=%%g)
for /F "tokens=3 delims= " %%a in ("%VAR%") do (
   SET VAR=%%a
)
echo:%VAR%
pause
magick %1 -transparent %VAR% %1
pause