mkdir %1_frames
ffmpeg -i %1 -r 24 -vf "setpts=(4/1)*PTS" %1_frames\output.mp4
ffmpeg -i %1_frames\output.mp4 -vf "select=not(mod(n\,12))" -vsync vfr %1_frames\out%%d.png
REM for specific frames: ,select='between(t,37,45)' 
pause