#
# Sublime 2 plugin for quick sync with destination over SSH
#
# @copyleft (cl) 2013 WARP
# @version 0.0.1
# @licence GPL
# @link http://www.warp.lv/
#

import sublime, sublime_plugin
import subprocess
import threading
import re
import sys
import glob
import os
import json
from pprint import pprint


def loadSyncSettings(settingpath):
    with open(settingpath) as data_file:    
        data = json.load(data_file)
    return data

def runSync(cmd):
    #print cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while (True):
        retcode = p.poll()
        line    = p.stdout.readline()
        yield line.decode('utf-8')
        if (retcode is not None):
            break

  
class WarpThreadedSync(threading.Thread):
    def __init__(self, _settings, _projFolder):
        self.settings    = _settings
        self.projFolder  = _projFolder
        threading.Thread.__init__(self)

    def run(self):
        # add delete so that if file is removed locally it is also removed from the server
        excludeStrComp = ""
        for exclude in self.settings["warpsync"][0]["excludes"]:
            excludeStrComp+="--exclude="
            excludeStrComp+='\''+str(exclude)+'\' '

        deleteIfNotLocal = "--delete " if (int(self.settings["warpsync"][0]["opts"][0]["delifnotonlocal"]) == 1) else ""
        deleteExcluded = "--delete-excluded " if (int(self.settings["warpsync"][0]["opts"][0]["deleteexcluded"]) == 1) else ""

        remoteHost = str(self.settings["warpsync"][0]["connection"][0]["host"])
        remotePort = str(self.settings["warpsync"][0]["connection"][0]["port"])
        remoteUser = str(self.settings["warpsync"][0]["connection"][0]["username"])
        remotePath = str(self.settings["warpsync"][0]["connection"][0]["remotepath"])

        cmd = 'rsync --progress -vv -az -e \'ssh -p ' + remotePort + '\' ' + deleteIfNotLocal + excludeStrComp + deleteExcluded + self.projFolder + '/' + ' ' + remoteUser + '@' + remoteHost + ':' + remotePath
        
        print "WARPSYNC | start"

        #os.system(cmd)
        for line in runSync(cmd):
            print line,

        print "WARPSYNC | done"

        if ( int(self.settings["warpsync"][0]["connection"][0]["openuri"]) == 1):
            os.system('open \'' + str(self.settings["warpsync"][0]["connection"][0]["remoteuri"]) + '\'')


class WarpSyncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        #self.window.active_view().insert(edit, 0, "inview")
        print "WARPSYNC | starting"
        currWindow = self.view.window()
        folders = currWindow.folders()
        foldersLen = len(folders)
        if (foldersLen > 1):
            print "WARPSYNC | more than one folder at project top level found, aborting"
            for folder in folders:
                print folder
            print "WARPSYNC | abort"
            return
        elif (foldersLen == 0):
            print "WARPSYNC | there must be one top level directory, aborting"
            return
        else:
            projFolder = str(folders[0])
            print "WARPSYNC | project folder: " + projFolder;
            #find project file
            projFileSearch = glob.glob(projFolder+'/*.sublime-project')
            if (len(projFileSearch) != 1):
                "WARPSYNC | no sublime-project file found in top directory" 
                return
            projFilePath =  str(projFileSearch[0])
            print "WARPSYNC | project file: " + projFilePath

            settings = loadSyncSettings(projFilePath)
            #pprint(settings)

            if ( str(settings["folders"][0]["path"]) != str(projFolder) ):
                print "WARPSYNC | physical folder differs from sublime-procect path entry! todo.."

            WarpThreadedSync(settings, projFolder).start()



