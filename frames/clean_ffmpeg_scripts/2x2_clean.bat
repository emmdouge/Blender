set draw_box="drawbox=x=in_w/2-in_w/(10*2):y=in_h/2-in_h/(10*2):w=in_w/10:h=in_h/10:color=green@0.5:t=fill"
mkdir %1_2sframes
ffmpeg -i %1 -r 24 %1_2sframes\output_true24fps.mp4 
ffmpeg -i %1_2sframes\output_true24fps.mp4 -vf %draw_box% %1_2sframes\outputN.mp4 
ffmpeg -i %1_2sframes\output_true24fps.mp4 -i %1_2sframes\outputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_2sframes\output24b.mp4
ffmpeg -i %1_2sframes\output24b.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_2sframes\out%%d.png
ffmpeg -r 12 -f image2 -s 1920x1080 -i %1_2sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_2sframes\test.mp4
ffmpeg -i %1_2sframes\output24b.mp4 -i %1_2sframes\output_true24fps.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,13)),0)'" %1_output2s.mp4

mkdir %1_3sframes
ffmpeg -i %1_2sframes\output_true24fps.mp4 -vf "select=not(mod(n\,3))" -vsync vfr %1_3sframes\tmp%%d.png
ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_3sframes\tmp%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_3sframes\input_true8fps.mp4 
ffmpeg -i %1_3sframes\input_true8fps.mp4 -r 16 %1_3sframes\output_true16fps.mp4
ffmpeg -i %1_3sframes\output_true16fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_3sframes\out%%d.png
ffmpeg -r 8 -f image2 -s 1920x1080 -i %1_3sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_3sframes\testb2.mp4
ffmpeg -i %1_3sframes\testb2.mp4 -r 24 %1_3sframes\test_true24fps.mp4
ffmpeg -i %1_3sframes\test_true24fps.mp4 -vf %draw_box% %1_3sframes\inputN.mp4 
ffmpeg -i %1_3sframes\test_true24fps.mp4 -i %1_3sframes\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_output3s.mp4 

mkdir %1_4sframes
ffmpeg -i %1_2sframes\output_true24fps.mp4 -vf "select=not(mod(n\,4))" -vsync vfr %1_4sframes\tmp%%d.png
ffmpeg -r 6 -f image2 -s 1920x1080 -i %1_4sframes\tmp%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_4sframes\input_true6fps.mp4 
ffmpeg -i %1_4sframes\input_true6fps.mp4 -r 12 %1_4sframes\output_true12fps.mp4
ffmpeg -i %1_4sframes\output_true12fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_4sframes\out%%d.png
ffmpeg -r 6 -f image2 -s 1920x1080 -i %1_4sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_4sframes\testb2.mp4
ffmpeg -i %1_4sframes\testb2.mp4 -r 24 %1_4sframes\test_true24fps.mp4
ffmpeg -i %1_4sframes\test_true24fps.mp4 -vf %draw_box% %1_4sframes\inputN.mp4 
ffmpeg -i %1_4sframes\test_true24fps.mp4 -i %1_4sframes\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_output4s.mp4 

mkdir %1_6sframes
ffmpeg -i %1_2sframes\output_true24fps.mp4 -vf "select=not(mod(n\,6))" -vsync vfr %1_6sframes\tmp%%d.png
ffmpeg -r 4 -f image2 -s 1920x1080 -i %1_6sframes\tmp%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_6sframes\input_true4fps.mp4 
ffmpeg -i %1_6sframes\input_true4fps.mp4 -r 8 %1_6sframes\output_true8fps.mp4 
ffmpeg -i %1_6sframes\output_true8fps.mp4 -vf "select=not(mod(n\,2))" -vsync vfr %1_6sframes\out%%d.png
ffmpeg -r 4 -f image2 -s 1920x1080 -i %1_6sframes\out%%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p %1_6sframes\testb2.mp4
ffmpeg -i %1_6sframes\testb2.mp4 -r 24 %1_6sframes\test_true24fps.mp4
ffmpeg -i %1_6sframes\test_true24fps.mp4 -vf %draw_box% %1_6sframes\inputN.mp4 
ffmpeg -i %1_6sframes\test_true24fps.mp4 -i %1_6sframes\inputN.mp4 -filter_complex "[0:v]scale=1280x720[bottom];[1:v]scale=1280x720[top];[bottom][top]overlay=enable='if(gt(n,0),not(mod(n\,12)),0)'" %1_output6s.mp4 


ffmpeg -i %1_output2s.mp4 -i %1_output3s.mp4 -i %1_output4s.mp4 -i %1_output6s.mp4 -filter_complex "[0:v][1:v][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]" -map "[v]" %1_output.mp4
ffmpeg -stream_loop 3 -i %1_output.mp4 -c copy %1_output_loop.mp4