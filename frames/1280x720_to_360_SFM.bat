mkdir %1_360_sfm_frames
ffmpeg -i %1 -r 12 -y %1_360_sfm_frames\input.mp4
ffmpeg -i %1_360_sfm_frames\input.mp4 -filter:v scale=1280:720,crop=720:720:279:0 %1_360_sfm_frames\output.mp4
ffmpeg -i %1_360_sfm_frames\output.mp4 -vf fps=24,scale=360:360,select=1 -vsync 0 %1_360_sfm_frames\out%%d.png
pause