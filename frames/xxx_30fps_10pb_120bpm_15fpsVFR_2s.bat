mkdir %1_frames
ffmpeg -i %1 -vf negate %1_frames\outputN.mp4 
ffmpeg -i %1 -i %1_frames\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,15)),0)'" %1_frames\output15b.mp4
ffmpeg -i %1_frames\output15b.mp4 -vf "setpts=(10/1)*PTS" %1_frames\output10pp.mp4
REM 600/300 = 30s, 150 = 15s, 30 = 3s, 20 = 2s, 10 = 1s ------ 10b = 15s, 2bs = 3s, 4bps = 6s
ffmpeg -i %1_frames\output10pp.mp4 -vf "select=not(mod(n\,20))" -vsync vfr %1_frames\out%%d.png
pause