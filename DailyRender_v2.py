from P4 import P4, P4Exception
import urllib.request
import json
import subprocess
import os
import shutil
import datetime
import time
from pathlib import Path


from tendo import singleton
me = singleton.SingleInstance()

def newest(path):
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    return max(paths, key=os.path.getctime)


render_engines = {
    'UE_4.25': r"C:\Program Files\Epic Games\UE_4.25\Engine\Binaries\Win64\UE4Editor.exe",
    'UE_4.26': r"C:\Program Files\Epic Games\UE_4.26\Engine\Binaries\Win64\UE4Editor.exe",
    'UE_4.27': r"C:\Program Files\Epic Games\UE_4.27\Engine\Binaries\Win64\UE4Editor.exe",
    'UE_5.0': r"C:\Program Files\Epic Games\UE_5.0\Engine\Binaries\Win64\UnrealEditor.exe",
    'UE_5.1': r"C:\Program Files\Epic Games\UE_5.1\Engine\Binaries\Win64\UnrealEditor.exe",
    'TL_4.25': r"C:\UE4\UnrealEngine4_25\Engine\Binaries\Win64\UE4Editor.exe"
}

#ffmpeg = r"C:\Program Files\ImageMagick-7.0.11-Q16-HDRI\ffmpeg.exe"
ffmpeg = r"\\cinemaserver\Tcinema\VTLIB\apps\FFMPEG\bin\ffmpeg.exe"

server_address = "http://vaalt/daily/"
data_string = urllib.request.urlopen(server_address).read()
jobs = json.loads(data_string)


p4 = P4()
p4.port = "cinema:1666"
p4.user = "Tech_T"
p4.password = "Tech_T_pass"
p4.exception_level = 1
p4.connect()

today = datetime.date.today().strftime("%Y%m%d")


for job in jobs:
    is_activated = job['activate']
    host = job['host']
    if not is_activated or host != 1:
        continue
    try:
        render_engine = render_engines[job['engine_version']]
        uproject_res = p4.run("where", job['ue_project'])
        uproject_path = uproject_res[0]['path']
        uproject_local_path = os.path.dirname(uproject_res[0]['depotFile'])
        p4.run("sync", uproject_local_path + "/...")

        umap_path = job['ue_umap']
        seq_path = job['ue_sequence']
        project_name = job['project_name']
        render_name = job['render_name'] + f"_{today}"
        custom_start = job.get('custom_start', 1)
        daily_path = job['output_directory']

        if "\\\\cinemaserver\\Tcinema\\9_Daily" in daily_path:
            daily_path = f"\\\\cinemaserver\\Tcinema\\9_Daily\\{today}".replace("\\\\cinemaserver\\Tcinema", "T:")
        else:
            daily_path = f"{daily_path}\\{today}".replace("\\\\cinemaserver\\Tcinema", "T:")
        
        if not os.path.exists(daily_path):
            os.makedirs(daily_path)

        print(f"Daily Path : {daily_path}")

        movie_path = f"D:/DAILYRENDER/{today}"
        render_path = f"D:/DAILYRENDER/{project_name}/{today}"

        if not os.path.exists(movie_path):
            os.makedirs(movie_path)

        if not os.path.exists(render_path):
            os.makedirs(render_path)

        resx = job['res_x']
        resy = job['res_y']

        # render_warmup = job['render_warmup']

        render_command = f'"{render_engine}" "{uproject_path}" {umap_path} -game -unattended -MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor'
        render_command += ' -ExecutorPythonClass=/Engine/PythonTypes.MoviePipelineExampleRuntimeExecutor '
        render_command += f'-LevelSequence="{seq_path}" -OutputDirectory="{render_path}" -OutputName="{render_name}" -ResX=1920 -ResY=1080 -RenderResX={resx} -RenderResY={resy} -MovieWarmUpFrames=100 -MovieDelayBeforeWarmUp=1 -log -notexturestreaming -windowed'
        if render_engine.startswith("4"):
            render_command += ' -dx11'

        render_command = render_command.replace("\\", "\\\\")
        subprocess.call(render_command)

        print(render_command)

        logPath = os.path.dirname(uproject_path) + "\\Saved\\Logs"
        logFile = newest(logPath)

        if os.path.isfile(logFile):
            try:
                shutil.move(logFile, f"T:\\9_Daily\\_RENDER\\Logs\\{render_name}_render.log")
            except:
                pass

        ffmpeg_command = f"\"{ffmpeg}\" -framerate 30 -start_number {custom_start} -i \"{render_path}\\{render_name}.%04d.png\""
        #ffmpeg_command += " -vcodec mpeg4 -b:v 128M -preset slow -y "
        ffmpeg_command += " -y -probesize 5000000 -c:v libx264 -g 1 -tune stillimage -crf 19 -bf 0 -vendor apl0 -pix_fmt yuv420p "
        ffmpeg_command += f"\"{movie_path}\\{render_name}.mp4\""
        
        subprocess.call(ffmpeg_command)

        if os.path.isfile(f"{movie_path}\\{render_name}.mp4"):
            try:
                shutil.copy(f"{movie_path}\\{render_name}.mp4", f"{daily_path}\\{render_name}.mp4")
            except:
                pass
        time.sleep(300)

    except IndexError:
        print("no render_engine")

#C:\Program Files\Epic Games\UE_4.25\Engine\Binaries\Win64\UE4Editor.exe
#"D:\\\\depot\\Universe\\Universe_MV\\Universe_MV.uproject" "/Game/VisualTech/Map/ATEEZ_P" -game -MovieSceneCaptureType="/Script/MovieSceneCapture.AutomatedLevelSequenceCapture" -LevelSequence="/Game/VisualTech/Seq/1_ATEEZ/ATEEZ_master" -MovieFrameRate=30 -MovieFolder="T:\\9_Daily\\_RENDER\\Universe_MV\\20201012" -MovieName="1_ATEEZ_20201012" -noloadingscreen -ResX=1920 -ResY=1080 -ForceRes -MovieFormat=PNG -MovieQuality=100 -notexturestreaming -MovieCinematicMode=yes -NoScreenMessages -windowed -MovieWarmUpFrames=60

# print(jobs)

