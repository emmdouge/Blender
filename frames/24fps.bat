mkdir %1_frames
ffmpeg -i %1 -r 24 %1_frames\output24fps.mp4 
REM ffmpeg -i %1_frames\output12b.mp4 -r 24 -vf "setpts=(4/1)*PTS" %1_frames\output25pp.mp4
REM for specific frames: ,select='between(t,37,45)' 
REM to make first frame the original instead of negative overlay=enable='if(gt(n,0),not(mod(n\,64)),0)'
pause