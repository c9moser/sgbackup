###############################################################################
# sgbackup - The SaveGame Backup tool                                         #
#    Copyright (C) 2024  Christian Moser                                      #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.   #
###############################################################################

import os
import re
from pathlib import Path
import sys
import json

from .settings import settings

PLATFORM_WINDOWS = (sys.platform.lower() == 'win32')


from gi.repository.GObject import GObject,Property,Signal


class AcfFileParser(object):
    """
    Parses steam acf files to a dict.
    """
    def __init__(self):
        pass
    
    def __parse_section(self,lines:list):
        option_pattern = re.compile("^\"(.+)\"([ \\t]+)\"(.*)\"$")
        section_pattern = re.compile("^\"(.+)\"")
        line_count = 0
        ret = {}
        
        line_count=0
        while line_count < len(lines):
            line = lines[line_count]
            line_count+=1
            
            if line == '}':
                break
            
            s=line.strip()
            match = option_pattern.fullmatch(line)
            if match:
                name=line[match.start(1):match.end(1)]
                value=line[match.start(3):match.end(3)]
                ret[name] = value
            else:
                match2 = section_pattern.fullmatch(line)
                if match2:
                    name=line[match2.start(1):match2.end(1)]
                    if lines[line_count] == '{':
                        line_count += 1
                        n_lines,sect = self.__parse_section(lines[line_count:])
                        line_count += n_lines
                        ret[name]=sect
            
                
        return line_count,ret
                
                
    
    def parse_file(self,acf_file)->dict:
        if not os.path.isfile(acf_file):
            raise FileNotFoundError("File \"{s}\" does not exist!")
        
        with open(acf_file,'r') as ifile:
            buffer = ifile.read()
        lines = [l.strip() for l in buffer.split('\n')]
        if lines[0] == "\"AppState\"" and lines[1] == "{":
            n_lines,sect = self.__parse_section(lines[2:])
            return sect
        
        raise RuntimeError("Not a acf file!")

class IgnoreSteamApp(GObject):
    @staticmethod
    def new_from_dict(conf:dict):
        if ('appid' in conf and 'name' in conf):
            appid = conf['appid']
            name = conf['name']
            reason = conf['reason'] if 'reason' in conf else ""
            return SteamIgnoreApp(appid,name,reason)
            
        return None
    
    def __init__(self,appid:int,name:str,reason:str):
        GObject.__init__(self)
        self.__appid = int(appid)
        self.__name = name
        self.__reason = reason
        
    @Property(type=int)
    def appid(self)->str:
        return self.__appid
    
    @Property(type=str)
    def name(self)->str:
        return self.__name
    @name.setter
    def name(self,name:str):
        self.__name = name

    @Property(type=str)
    def reason(self)->str:
        return self.__reason
    @reason.setter
    def reason(self,reason:str):
        self.__reason = reason
        

    def serialize(self):
        return {
            'appid': self.appid,
            'name': self.name,
            'reason': self.reason,
        }

class SteamApp(GObject):
    def __init__(self,appid:int,name:str,installdir:str):
        GObject.__init__(self)
        self.__appid = int(appid)
        self.__name = name
        self.__installdir = installdir
        
    @Property(type=int)
    def appid(self):
        return self.__appid
    
    @Property
    def name(self):
        return self.__name
    
    @Property
    def installdir(self):
        return self.__installdir
    
    def __str__(self):
        return '{}: {}'.format(self.appid,self.name)
    
    def __gt__(self,other):
        return self.appid > other.appid
    
    def __lt__(self,other):
        return self.appid < other.appid
    
    def __eq__(self,other):
        return self.appid == other.appid
    

class SteamLibrary(GObject):
    def __init__(self,library_path:str):
        GObject.__init__(self)
        self.directory = library_path
        
    @Property(type=str)
    def directory(self):
        return self.__directory
    
    @directory.setter
    def directory(self,directory:str):
        if not os.path.isabs(directory):
            raise ValueError("\"directory\" is not an absolute path!")
        if not os.path.isdir(directory):
            raise NotADirectoryError("\"{}\" is not a directory or does not exist!".format(directory))
        
        self.__directory = directory
        
    @Property
    def path(self)->Path:
        return Path(self.directory).resolve()
    
    @Property
    def steam_apps(self)->list:
        parser = AcfFileParser()
        appdir = self.path / "steamapps"
        commondir = appdir / "common"
        
        ret = []
        for acf_file in appdir.glob('appmanifest_*.acf'):
            if not acf_file.is_file():
                continue
            try:
                data = parser.parse_file(str(acf_file))
                app = SteamApp(data['appid'],data['name'],str(commondir/data['installdir']))
                ret.append(app)
            except:
                pass
            
        return sorted(ret)
    
class Steam(GObject):
    def __init__(self):
        GObject.__init__(self)
        self.__libraries = []
        self.__ignore_apps = []
                
        if not self.steamlib_list_file.is_file():
            if (PLATFORM_WINDOWS):
                libdirs=[
                    "C:\\Program Files (x86)\\steam",
                    "C:\\Program Files\\steam",
                ]
                for i in libdirs:
                    if (os.path.isdir(i)):
                        self.__libraries.append(SteamLibrary(i))
                        break
        else:
            with open(str(self.steamlib_list_file),'r',encoding="utf-8") as ifile:
                for line in (i.strip() for i in ifile.readlines()):
                    if not line or line.startswith('#'):
                        continue
                    libdir = Path(line).resolve()
                    if libdir.is_dir():
                        try:
                            self.add_library(str(libdir))
                        except:
                            pass
        
        ignore_apps = []
        if self.ignore_apps_file.is_file():
            with open(str(self.ignore_apps_file),'r',encoding="utf-8") as ifile:
                ignore_list = json.loads(ifile.read())
            for ignore in ignore_list:
                try:
                    ignore_app = IgnoreSteamApp.new_from_dict(ignore)
                except:
                    continue
                if ignore_app:
                        self.__ignore_apps.append(ignore_app)
            self.__ignore_apps = sorted(ignore_apps)            
    #__init__()     

    @Property
    def steamlib_list_file(self)->Path:
        return Path(settings.config_dir).resolve() / 'steamlib.lst'
    
    @Property
    def ignore_apps_file(self)->Path:
        return Path(settings.config_dir).resolve / 'ignore_steamapps.json'
    
    @Property
    def libraries(self):
        return self.__libraries
    
    @Property
    def ignore_apps(self):
        return self.__ignore_apps
    
    def __write_steamlib_list_file(self):
        with open(self.steamlib_list_file,'w',encoding='utf-8') as ofile:
            ofile.write('\n'.join(str(sl.directory) for sl in self.libraries))
            
    def add_library(self,steamlib:SteamLibrary|str):
        if isinstance(steamlib,SteamLibrary):
            lib = steamlib
        else:
            lib = SteamLibrary(steamlib)
        
        lib_exists = False    
        for i in self.libraries:
            if i.derctory == lib.directory:
                lib_exists = True
                break
            
        if not lib_exists:
            self.__libraries.append(lib)
        self.__write_steamlib_list_file()
        
    def remove_library(self,steamlib:SteamLibrary|str):
        if isinstance(steamlib,SteamLibrary):
            libdir = steamlib.directory
        else:
            libdir = str(steamlib)
            
        delete_libs=[]
        for i in range(len(self.__libraries)):
            if self.__libraries[i].directory == libdir:
                delete_libs.append(i)
        
        if delete_libs:        
            for i in sorted(delete_libs,reverse=True):
                del self.__libraries[i]
            self.__write_steamlib_list_file()
