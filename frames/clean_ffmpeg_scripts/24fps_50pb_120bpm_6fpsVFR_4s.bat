mkdir %1_frames
ffmpeg -i %1 -r 24 %1_frames\input_true24fps.mp4 
ffmpeg -i %1 -r 12 %1_frames\output_true12fps.mp4 
REM ffmpeg -i %1_frames\output_true12fps.mp4 -r 24 %1_frames\output_true24fps.mp4 
ffmpeg -i %1_frames\output_true12fps.mp4 -vf negate %1_frames\outputN.mp4 
ffmpeg -i %1_frames\output_true12fps.mp4 -i %1_frames\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,6)),0)'" %1_frames\output12b.mp4
ffmpeg -i %1_frames\output12b.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_frames\in%%d.png
ffmpeg -i %1_frames\output_true12fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_frames\out%%d.png
REM ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_frames\in%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_frames\testb.mp4
ffmpeg -r 6 -f image2 -s 1920x1080 -i %1_frames\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_frames\testb2.mp4
ffmpeg -i %1_frames\testb2.mp4 -r 24 %1_frames\test_true24fps.mp4
ffmpeg -i %1_frames\test_true24fps.mp4 -vf negate %1_frames\inputN.mp4 
ffmpeg -i %1_frames\test_true24fps.mp4 -i %1_frames\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_frames\testp1.mp4
ffmpeg -i %1_frames\testp1.mp4 -vf negate %1_frames\output4s.mp4 
REM ffmpeg -i %1_frames\output30b.mp4 -r 24 -vf "setpts=(2/1)*PTS" %1_frames\output25pp.mp4
REM for specific frames: ,select='between(t,37,45)' 
REM to make first frame the original instead of negative overlay=enable='if(gt(n,0),not(mod(n\,64)),0)'
pause