import picamera
import datetime
import os
import threading

"""
Folder
"""
class Folder_control(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def getDir(self,path='.'):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += getDir(entry.path)
        return total

    def Unit(self,unit):
        units = ['B', 'K', 'M', 'G', 'T']
        val = units.index(unit)
        if val <= 0:
            return 1
        else:
            return 1024 ** (val)
    
    def RemoveFile(self, path):
        files_list = os.listdir(path)
        if not files_list:
            pass
        else:
            files = files_list[0]
            os.remove(path+'/'+files)

"""
Recoring
"""
savepath = '/home/pi/MakeRaspAgain/VideoRecord'

class Recording(threading.Thread):
    camera = picamera.PiCamera()
    camera.resolution = (1280,720)
    camera.framerate = 30
    recording_time = 3600 # 1 hour

    def __init__(self):
        threading.Thread.__init__(self)

    def recordOneHour(self):
        now = datetime.datetime.now()
        filename = now.strftime('%Y-%m-%d %H:%M')
        self.camera.start_recording(output = savepath+'/'+filename+'.h264')
        self.camera.wait_recording(self.recording_time)
        self.camera.stop_recording()
   
"""
main
"""
get_dir = Folder_control()

while True:
    used_space = (get_dir.getDir(savepath) / get_dir.Unit('G'))
    if used_space > 3.0:
        get_dir.RemoveFile(savepath)
    else:
        Recording().recordOneHour()
    
