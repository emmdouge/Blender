mkdir %1_frames
ffmpeg -i %1 -r 6 -y %1_frames\output.mp4
ffmpeg -i %1_frames\output.mp4 -vf fps=24,scale=1280:720,select=1  -vsync 0 %1_frames\out%%d.png
REM for specific frames: ,select='between(t,37,45)' 
pause