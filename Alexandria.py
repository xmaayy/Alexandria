import win32api
import sqlite3
import subprocess
import os
import logging
import string
import re

## CONFIGURING DEBUG INFO LOGGING ##
logger = logging.getLogger('Alexandria')
handler = logging.FileHandler('C:\Alexandria\log.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

#Creating a class for the hard disks
class Disk(object): #This just makes it so much easier to pass disks
    def __init__(self,ini_serial,ini_name,ini_letter):
        self.serial = ini_serial
        self.name = ini_name
        self.letter = ini_letter

def get_file_res(location):
    #Get the resolution of the video file at the given location
    #This function return 2 values, the first is the width of the video, the second is the height
    probe_return = (subprocess.check_output("ffprobe.exe -v error -of flat=s=_ -select_streams v:0 -show_entries stream=height,width \""+location+"\"",shell=True)).decode("utf-8")
    probe_return = probe_return.replace("streams_stream_0_","")
    decimals = re.compile('\d+(?:\.\d+)?')
    dim = decimals.findall(probe_return)

    return (dim[0],dim[1])


def get_drive_names():
    #Get the letters of actual hard drives for da user
    #This function return 1 array of Disks, the size depends on the number of assigned drive letters
    disks = win32api.GetLogicalDriveStrings()
    disks = disks.strip().split(':\\\x00')

    #disks = disks.translate({ord(c): None for c in ':\\ '})# THESE SPACES WONT GO AWAY
    #disks = re.sub(r'\s+','',disks, flags=re.UNICODE)      #THIS FUNCTION WOULDNT BE NEEDED IF THEY WOULD GO AWAY
    drive = []
    
    for i in range(len(disks)): # or just disks without the other stuff
        logger.debug('Trying drive: '+disks[i])
        try:
            temp1,temp2,_,_,_ = win32api.GetVolumeInformation(disks[i]+':\\')
            logger.info('Got info for drive: ' + temp1)
            drive.append(Disk(temp2,temp1,disks[i]+':\\'))            
            logger.debug("Added a disk to drive list")

        except Exception as details:
            logger.debug(disks[i]+' is not a hard drive')
        
    return drive;
#****** END OF GET_DRIVE_NAMES *******

def walk_dir(drive):
    ext = [".3g2", ".3gp", ".asf", ".asx", ".avi", ".flv", \
                        ".m2ts", ".mkv", ".mov", ".mp4", ".mpg", ".mpeg", \
                        ".rm", ".swf", ".vob", ".wmv"]
    for root, dirs, files in os.walk(drive.letter):
        for name in files:
            if name.endswith(tuple(ext)):
                res= get_file_res(os.path.join(root, name))
                print(name + " Res: " + res[1] + 'p')
    


print('You have the following hard disks: ')
drives = get_drive_names()
for drive in drives:
    print(drive.letter + ' ' + drive.name + ' ' + str(drive.serial))

walk_dir(drives[1])
