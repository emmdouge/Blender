mkdir %1_frames
ffmpeg -i %1 -vf "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" %1_frames\30fpsInt.mp4