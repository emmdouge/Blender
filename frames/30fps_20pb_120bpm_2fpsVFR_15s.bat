mkdir %1_frames
ffmpeg -i %1 -vf negate %1_frames\outputN.mp4 
ffmpeg -i %1 -i %1_frames\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,30)),0)'" %1_frames\output30b.mp4
ffmpeg -i %1_frames\output30b.mp4 -vf "setpts=(10/2)*PTS" %1_frames\output20pp.mp4
REM 150 = 30s, 75 = 15s, 15 = 3s, 10 = 2s, 5 = 1s ------ 10b = 30s, 1b = 3s, 2bp = 6s, 5bp = 15s
ffmpeg -i %1_frames\output20pp.mp4 -vf "select=not(mod(n\,75))" -vsync vfr %1_frames\out%%d.png
cd %1_frames
ffmpeg -framerate 10 -start_number 1 -i out%%d.png -vcodec libx264 -pix_fmt yuv420p output10fps.mp4
ffmpeg -i %1_frames\output10fps.mp4 -vf "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" %1_frames\output10fpsInt.mp4
pause