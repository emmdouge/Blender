mkdir %1_4sframes
ffmpeg -i %1 -r 24 %1_4sframes\input_true24fps.mp4 
ffmpeg -i %1 -r 12 %1_4sframes\output_true12fps.mp4 
REM ffmpeg -i %1_4sframes\output_true12fps.mp4 -r 24 %1_4sframes\output_true24fps.mp4 
ffmpeg -i %1_4sframes\output_true12fps.mp4 -vf negate %1_4sframes\outputN.mp4 
ffmpeg -i %1_4sframes\output_true12fps.mp4 -i %1_4sframes\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,6)),0)'" %1_4sframes\output12b.mp4
ffmpeg -i %1_4sframes\output12b.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_4sframes\in%%d.png
ffmpeg -i %1_4sframes\output_true12fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_4sframes\out%%d.png
REM ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_4sframes\in%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_4sframes\testb.mp4
ffmpeg -r 6 -f image2 -s 1920x1080 -i %1_4sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_4sframes\testb2.mp4
ffmpeg -i %1_4sframes\testb2.mp4 -r 24 %1_4sframes\test_true24fps.mp4
ffmpeg -i %1_4sframes\test_true24fps.mp4 -vf negate %1_4sframes\inputN.mp4 
ffmpeg -i %1_4sframes\test_true24fps.mp4 -i %1_4sframes\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_4sframes\testp1.mp4
ffmpeg -i %1_4sframes\testp1.mp4 -vf negate output4s.mp4 
REM ffmpeg -i %1_4sframes\output30b.mp4 -r 24 -vf "setpts=(2/1)*PTS" %1_4sframes\output25pp.mp4
REM for specific frames: ,select='between(t,37,45)' 
REM to make first frame the original instead of negative overlay=enable='if(gt(n,0),not(mod(n\,64)),0)'
pause