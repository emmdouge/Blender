mkdir %1_2sframes
ffmpeg -i %1 -r 24 %1_2sframes\output_true24fps.mp4 
ffmpeg -i %1_2sframes\output_true24fps.mp4 -vf negate %1_2sframes\outputN.mp4 
ffmpeg -i %1_2sframes\output_true24fps.mp4 -i %1_2sframes\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_2sframes\output24b.mp4
ffmpeg -i %1_2sframes\output24b.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_2sframes\out%%d.png
ffmpeg -r 12 -f image2 -s 1920x1080 -i %1_2sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_2sframes\test.mp4
ffmpeg -i %1_2sframes\output24b.mp4 -i %1_2sframes\output_true24fps.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,13)),0)'" output2s.mp4

mkdir %1_3sframes
ffmpeg -i %1 -r 24 %1_3sframes\input_true24fps.mp4 
ffmpeg -i %1 -r 16 %1_3sframes\output_true16fps.mp4 
REM ffmpeg -i %1_3sframes\output_true16fps.mp4 -r 24 %1_3sframes\output_true24fps.mp4 
ffmpeg -i %1_3sframes\output_true16fps.mp4 -vf negate %1_3sframes\outputN.mp4 
ffmpeg -i %1_3sframes\output_true16fps.mp4 -i %1_3sframes\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,8)),0)'" %1_3sframes\output16b.mp4
ffmpeg -i %1_3sframes\output16b.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_3sframes\in%%d.png
ffmpeg -i %1_3sframes\output_true16fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_3sframes\out%%d.png
REM ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_3sframes\in%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_3sframes\testb.mp4
ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_3sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_3sframes\testb2.mp4
ffmpeg -i %1_3sframes\testb2.mp4 -r 24 %1_3sframes\test_true24fps.mp4
ffmpeg -i %1_3sframes\test_true24fps.mp4 -vf negate %1_3sframes\inputN.mp4 
ffmpeg -i %1_3sframes\test_true24fps.mp4 -i %1_3sframes\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_3sframes\testp1.mp4
ffmpeg -i %1_3sframes\testp1.mp4 -vf negate output3s.mp4 

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

mkdir %1_6sframes
ffmpeg -i %1 -r 24 %1_6sframes\input_true24fps.mp4 
ffmpeg -i %1 -r 8 %1_6sframes\output_true8fps.mp4 
REM ffmpeg -i %1_6sframes\output_true8fps.mp4 -r 24 %1_6sframes\output_true24fps.mp4 
ffmpeg -i %1_6sframes\output_true8fps.mp4 -vf negate %1_6sframes\outputN.mp4 
ffmpeg -i %1_6sframes\output_true8fps.mp4 -i %1_6sframes\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,4)),0)'" %1_6sframes\output8b.mp4
ffmpeg -i %1_6sframes\output8b.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_6sframes\in%%d.png
ffmpeg -i %1_6sframes\output_true8fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_6sframes\out%%d.png
REM ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_6sframes\in%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_6sframes\testb.mp4
ffmpeg -r 4 -f image2 -s 1920x1080 -i %1_6sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_6sframes\testb2.mp4
ffmpeg -i %1_6sframes\testb2.mp4 -r 24 %1_6sframes\test_true24fps.mp4
ffmpeg -i %1_6sframes\test_true24fps.mp4 -vf negate %1_6sframes\inputN.mp4 
ffmpeg -i %1_6sframes\test_true24fps.mp4 -i %1_6sframes\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_6sframes\testp1.mp4
ffmpeg -i %1_6sframes\testp1.mp4 -vf negate output6s.mp4 


ffmpeg -i output2s.mp4 -i output3s.mp4 -i output4s.mp4 -i output6s.mp4 -filter_complex "[0:v][1:v][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]" -map "[v]" output.mp4