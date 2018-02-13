import glob
import moviepy.editor as mpy
# import imageio
# imageio.plugins.ffmpeg.download()

video_name = './png/tormenta'  ##nombre del archivo
fps = 1
file_list = glob.glob ('./png/*.png')  # obtiene los png de la ruta actual
# list.sort(file_list, key=lambda x: int(x.split('_')[1].split('.png')[0])) # Sort the images by #, this may need to be tweaked for your use case
clip = mpy.ImageSequenceClip (file_list, fps=fps)
clip.write_videofile ('{}.mp4'.format (video_name), fps=fps)