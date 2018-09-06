ffmpeg -i %1 -vf fps=24,scale=1280:720,select=1 -vsync 0 %1
pause