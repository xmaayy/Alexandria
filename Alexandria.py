import win32api
import sqlite3
import subprocess
import os
import logging
import string
import re
import sys

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

def walk_dir(drive,db_cursor):
    ext = [".3g2", ".3gp", ".asf", ".asx", ".avi", ".flv", \
                        ".m2ts", ".mkv", ".mov", ".mp4", ".mpg", ".mpeg", \
                        ".rm", ".swf", ".vob", ".wmv"]
    for root, dirs, files in os.walk(drive.letter):
        for name in files:
            if name.endswith(tuple(ext)) and root.find('$Recycle')==-1:
                try:
                    res = get_file_res(os.path.join(root, name))
                    logger.debug(name + " Res: " + res[1] + 'p')
                    logger.debug("INSERT INTO " + drive.name + " VALUES ('" + name + "'," + str(res[1]) + "," + '0' + "," + '0' + ")")
                    db_cursor.execute('INSERT INTO "' + drive.name + '" VALUES ("' + name + '",' + str(res[1]) + ',' + '0' + ',' + '0' + ')')
                except Exception as error:
                    logger.info('Bad File: '+os.path.join(root, name))

def scan():
    drives = get_drive_names()

    while 1:
        #See if they really do want each disk to be scanned
        print('\n\nYou have the following drives to be scanned: ')
        for drive_num in range(len(drives)):
            print(str(drive_num+1) + " " + drives[drive_num].letter + ' ' + drives[drive_num].name + ' ' + str(drives[drive_num].serial))

        exclude = input('Would you like to exclude any of these drives? If so, please enter its number now, or 0 to continue: ')
        if int(exclude,10):
            try:
                drives.pop(int(exclude,10)-1)
            except KeyError:
                print('Please input a number')
        else:
            break
            

    for drive in drives:
        connection = sqlite3.connect('Library.db')
        db_cursor = connection.cursor()
        db_cursor.execute("DROP TABLE IF EXISTS '"+drive.name+"'")
        connection.commit()
        try:
            db_cursor.execute("CREATE TABLE '" + drive.name + "' (name, resolution, size, age)")
            print ("Re/Created Drive Table")
        except sqlite3.Error as er:
            print (er)
        print("Cataloging disk " + drive.letter + " otherwise known as: " + drive.name)
        walk_dir(drive,db_cursor)
        connection.commit()

    db_cursor.close()

def search():
    drives = get_drive_names()
    connection = sqlite3.connect('Library.db')
    db_cursor = connection.cursor()

    term = input ("What would you like to search for? :   ")

    for drive in drives:
        try:
            for file in db_cursor.execute("SELECT * from '" + drive.name + "' WHERE name LIKE '%" + term + "%'"):
                print ("Name: " + file[0] + "\t\tResolution: " + str(file[1]) + 'p')
        except sqlite3.Error as er:
            print(er)
    

###############################################################################################################

print("Welcome to Alexandria! Version 0.01")

while 1:
    
    try:
        if(int(input("What would you like to do? 0-Scan   1-Search   :   "))):
            search()
        else:
            scan()
    except KeyError:
        print("That aint no number")

scan()
















