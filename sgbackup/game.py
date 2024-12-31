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

from gi.repository.GObject import Property,GObject,Signal,SignalFlags
from gi.repository import GLib

import os
import json
import re
import fnmatch

from enum import StrEnum
import sys
import logging
import pathlib

logger = logging.getLogger(__name__)

from .settings import settings

if sys.platform.lower() == "win32":
    PLATFORM_WIN32 = True
    import winreg
else:
    PLATFORM_WIN32 = False
    
if sys.platform.lower() in ['linux','freebsd','netbsd','openbsd','dragonfly']:
    PLATFORM_LINUX = True
else:
    PLATFORM_LINUX = False


class SavegameType(StrEnum):
    UNSET = "unset"
    OTHER = "other"
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    STEAM_WINDOWS = "steam_windows"
    STEAM_LINUX = "steam_linux"
    STEAM_MACOS = "steam_macos"
    GOG_WINDOWS = "gog_windows"
    GOG_LINUX = "gog_linux"
    EPIC_WINDOWS = "epic_windows"
    EPIC_LINUX = "epic_linux"
    
    @staticmethod
    def from_string(typestring:str):
        st=SavegameType
        s=typestring.lower()
        if (s == 'other'):
            return st.OTHER
        elif (s == 'windows'):
            return st.WINDOWS
        elif (s == 'linux'):
            return st.LINUX
        elif (s == 'macos'):
            return st.MACOS
        elif (s == 'steam_windows' or s == 'steamwindows' or s == 'steam.windows'):
            return st.STEAM_WINDOWS
        elif (s == 'steam_linux' or s == 'steamlinux' or s == 'steam.linux'):
            return st.STEAM_LINUX
        elif (s == 'steam_macos' or s == 'steammacos' or s == 'steam.macos'):
            return st.STEAM_MACOS
        elif (s == 'gog_winows' or s == 'gogwindows' or s == 'gog.windows'):
            return st.GOG_WINDOWS
        elif (s == 'gog_linux' or s == 'goglinux' or s == 'gog.linux'):
            return st.GOG_LINUX
        elif (s == 'epic_windows' or s == 'epicwindows' or s == 'epic.windows'):
            return st.EPIC_WINDOWS
        elif (s == 'epic_linux' or s == 'epiclinux' or s == 'epic.linux'):
            return st.EPIC_LINUX
        
        return st.UNSET
    

class GameFileType(StrEnum):
    GLOB = "glob"
    REGEX = "regex"
    FILENAME = "filename"
    
    @staticmethod
    def from_string(typestring:str):
        s = typestring.lower()
        if (s == 'glob'):
            return GameFileType.GLOB
        elif (s == 'regex'):
            return GameFileType.REGEX
        elif (s == 'filename'):
            return GameFileType.FILENAME
        
        raise ValueError("Unknown GameFileType \"{}\"!".fomrat(typestring))

class GameFileMatcher(GObject):
    def __init__(self,match_type:GameFileType,match_file:str):
        GObject.__init__(self)
        self.match_type = type
        self.match_file = match_file
    
    @Property
    def match_type(self)->GameFileType:
        return self.__match_type
    @match_type.setter
    def match_type(self,type:GameFileType):
        if not isinstance(type,GameFileType):
            raise TypeError("match_type is not a GameFileType instance!")
        self.__match_type = type
        
    @Property(type=str)
    def match_file(self)->str:
        return self.__match_file
    @match_file.setter
    def match_file(self,file:str):
        self.__match_file = file
    
    ## @}
    
    def match(self,rel_filename:str):
        def match_glob(filename):
            return fnmatch.fnmatch(filename,self.match_file)
        # match_glob()
        
        def match_filename(filename):
            if (PLATFORM_WIN32):
                fn = filename.replace("/","\\")
                if (self.match_file.endswith("\\")):
                    if fn == self.match_file[:-1] or fn.startswith(self.match_file):
                        return True
                elif fn == self.match_file:
                    return True
            else:
                    if (self.match_file.endswith('/')):
                        if fn == self.match_file[:-1] or fn.startswith(self.match_file):
                            return True
                    elif fn == self.match_file:
                        return True                        
            return False
        # match_filename()
        
        def match_regex(filename):
            return (re.search(self.match_file,filename) is not None)
        # match_filename()
        
        if (self.match_type == GameFileType.FILENAME):
            return match_filename(rel_filename)
        elif (self.match_type == GameFileType.GLOB):
            return match_glob(rel_filename)
        elif (self.match_type == GameFileType.REGEX):
            return match_regex(rel_filename)
        return False

class GameData(GObject):
    """
    :class: GameData
    :brief: Base class for platform specific data.
    """
    def __init__(self,
                 savegame_type:SavegameType,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        GObject.__init__(self)
        self.__savegame_type = savegame_type
        self.__savegame_root = savegame_root
        self.__savegame_dir = savegame_dir
        self.__variables = {}
        self.__filematch = []
        self.__ignorematch = []
        
        if variables is not None:
            variables.update(variables)
            
        if file_match is not None:
            for fm in file_match:
                self.add_file_match(fm)
                
        if ignore_match is not None:
            for fm in ignore_match:
                self.add_ignore_match(fm)
                        
    @Property
    def savegame_type(self)->SavegameType:
        """
        :attr: savegame_type
        :brief: Type of the class.
        """
        return self.__savegame_type
    
    @Property(type=str)
    def savegame_root(self)->str:
        """
        :attr: savegame_root
        """
        return self.__savegame_root
    
    @savegame_root.setter
    def savegame_root(self,sgroot:str):
        self.__savegame_root = sgroot
    
    @Property
    def savegame_dir(self)->str:
        """
        :attr: savegame_dir
        """
        return self.__savegame_dir
    
    @savegame_dir.setter
    def savegame_dir(self,sgdir:str):
        self.__savegame_dir = sgdir
        
    @Property
    def variables(self):
        return self.__variables
    
    @Property
    def file_match(self):
        return self.__filematch
    
    @Property
    def ignore_match(self):
        return self.__ignorematch
    
    def has_variable(self,name:str)->bool:
        return (name in self.__variables)
    
    def get_variable(self,name:str)->str:
        if name not in self.__variables:
            return ""
        return self.__variables[name]
        
    def set_variable(self,name:str,value:str):
        self.__variables[name] = value
        
    def delete_variable(self,name:str):
        if name in self.__variables:
            del self.__variables[name]
    
    def get_variables(self):
        return self.variables
    
    def match_file(self,rel_filename:str):
        if not self.__filematch:
            return True
        
        for fm in self.__filematch:
            if fm.match(rel_filename):
                return True
        return False
            
        
    def match_ignore(self,rel_filename:str):
        if not self.__ignorematch:
            return False
        
        for fm in self.__ignorematch:
            if fm.match(rel_filename):
                return True
        return False
    
    def match(self,rel_filename:str):
        if self.match_file(rel_filename) and not self.match_ignore(rel_filename):
            return True
        return False
    
    def add_file_match(self,matcher:GameFileMatcher):
        if not isinstance(matcher,GameFileMatcher):
            raise TypeError("matcher is not a \"GameFileMatcher\" instance!")
        self.__filematch.append(matcher)
        
    def remove_file_match(self,matcher:GameFileMatcher):
        for i in reversed(range(len(self.__filematch))):
            if (matcher == self.__filematch[i]):
                del self.__filematch[i]
    
    def add_ignore_match(self,matcher:GameFileMatcher):
        if not isinstance(matcher,GameFileMatcher):
            raise TypeError("matcher is not a \"GameFileMatcher\" instance!")
        self.__ignorematch.append(matcher)
        
    def remove_ignore_match(self,matcher:GameFileMatcher):
        for i in reversed(range(len(self.__ignorematch))):
            if (matcher == self.__ignorematch[i]):
                del self.__ignorematch[i]
                
    def serialize(self)->dict:
        ret = {
            'savegame_root': self.savegame_root,
            'savegame_dir': self.savegame_dir,
        }
        if (self.__variables):
            ret['variables'] = self.variables
        if (self.file_match):
            fm = []
            for matcher in self.file_match:
                fm.append({'type':matcher.match_type.value,'match':matcher.match_file})
            ret['file_match'] = fm
                
        if (self.add_ignore_match):
            im = []
            for matcher in self.ignore_match:
                im.append({'type':matcher.match_type.value,'match':matcher.match_file})
            ret['ignore_match'] = im
            
        return ret
                
class WindowsGame(GameData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 installdir:str|None=None,
                 game_registry_keys:str|list|None=None,
                 installdir_registry_keys:str|list|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        
        GameData.__init__(self,
                          SavegameType.WINDOWS,
                          savegame_root,
                          savegame_dir,
                          variables,
                          file_match,
                          ignore_match)
        if not installdir:
            self.__installdir = None
        else:
            self.__installdir = installdir
        
        if not game_registry_keys:
            self.__game_registry_keys = []
        elif isinstance(game_registry_keys,str):
            self.__game_registry_keys = [game_registry_keys]
        else:
            self.__game_registry_keys = list(game_registry_keys)
            
        if not installdir_registry_keys:
            self.__installdir_registry_keys = []
        elif isinstance(installdir_registry_keys,str):
            self.__installdir_registry_keys = [installdir_registry_keys]
        else:
            self.__installdir_registry_keys = list(installdir_registry_keys)
        
    def __get_hkey(self,regkey:str):
        regvec = regkey.split("\\")
        hkstr = regvec[0]
        if (hkstr == 'HKLM' or hkstr == 'HKEY_LOCAL_MACHINE'):
            return winreg.HKEY_LOCAL_MACHINE
        elif (hkstr == 'HKCU' or hkstr == 'HKEY_CURRENT_USER'):
            return winreg.HKEY_CURRENT_USER
        elif (hkstr == 'HKCC' or hkstr == 'HKEY_CURRENT_CONFIG'):
            return winreg.HKEY_CURRENT_CONFIG
        elif (hkstr == 'HKCR' or hkstr == 'HKEY_CLASSES_ROOT'):
            return winreg.HKEY_CLASSES_ROOT
        elif (hkstr == 'HKU' or hkstr == 'HKEY_USERS'):
            return winreg.HKEY_USERS
        return None
            
    @Property
    def installdir(self)->str|None:
        return self.__installdir
    
    @installdir.setter
    def installdir(self,installdir:str|None):
        self.__installdir = installdir
    
    @Property
    def game_registry_keys(self)->list:
        return self.__game_registry_keys
    
    @Property
    def installdir_registry_keys(self)->list:
        return self.__installdir_registry_keys
    
    @Property
    def is_installed(self)->bool|None:
        if not PLATFORM_WIN32 or not self.game_registry_keys:
            return None
        for regkey in self.__game_registry_keys:
            hkey = self.__get_hkey(regkey)
            regvec = regkey.split('\\')
            if (regvec > 1):
                key = '\\'.join(regvec[1:])
                try:
                    rkey = winreg.OpenKeyEx(hkey,key)
                    winreg.CloseKey(rkey)
                    return True
                except OSError as ex:
                    continue
                
        return False
    
    @Property
    def registry_installdir(self)->str|None:
        if not PLATFORM_WIN32 or not (self.installdir_registry_keys):
            return None
        for regkey in self.__game_registry_keys:
            hkey = self.__get_hkey(regkey)
            regvec = regkey.split('\\')
            if (regvec > 2):
                key = '\\'.join(regvec[1:-1])
                try:
                    rkey = None
                    rkey = winreg.OpenKeyEx(hkey,key)
                    retval = winreg.QueryValue(rkey,regvec[-1])
                    winreg.CloseKey(rkey)
                    if retval:
                        return str(retval[0])
                except OSError as ex:
                    if (rkey):
                        winreg.CloseKey(rkey)
                    continue
        return None
    
    def get_variables(self):
        variables = super().get_variables()
        variables["INSTALLDIR"] = self.installdir if self.installdir else ""
        
    def serialize(self):
        ret = super().serialize()
        if (self.installdir):
            ret['installdir'] = self.installdir
        if (self.game_registry_keys):
            ret['game_registry_keys'] = self.game_registry_keys
        if (self.installdir_registry_keys):
            ret['installdir_registry_keys'] = self.installdir_registry_keys
        return ret

class LinuxGame(GameData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 binary:str|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        GameData.__init__(self,
                          SavegameType.LINUX,
                          savegame_root,
                          savegame_dir,
                          variables,
                          file_match,
                          ignore_match)
        self.__binary = binary
        
    @Property
    def binary(self)->str|None:
        return self.__binary
    @binary.setter
    def binary(self,bin:str):
        self.__binary = bin
        
    @Property
    def is_installed(self)->bool|None:
        if PLATFORM_LINUX and self.binary:
            return bool(GLib.find_program_in_path(self.binary))
        else:
            return None
        
    def serialize(self):
        ret = super().serialize()
        if self.binary:
            ret['binary'] = self.binary
        return ret


class MacOSGame(GameData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 binary:str|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        GameData.__init__(self,
                          SavegameType.MACOS,
                          savegame_root,
                          savegame_dir,
                          variables,
                          file_match,
                          ignore_match)
        self.__binary = binary
        
    @Property
    def binary(self)->str|None:
        return self.__binary
    @binary.setter
    def binary(self,bin:str):
        self.__binary = bin
        
    @Property
    def is_installed(self)->bool|None:
        if PLATFORM_LINUX and self.binary:
            return bool(GLib.find_program_in_path(self.binary))
        else:
            return None
    
    def serialize(self):
        ret = super().serialize()
        if self.binary:
            ret['binary'] = self.binary
        return ret
    
    
class SteamGame(GameData):
    def __init__(self,
                 sgtype:SavegameType,
                 appid:int,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 installdir:str|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        if sgtype not in (SavegameType.STEAM_WINDOWS,
                          SavegameType.STEAM_LINUX,
                          SavegameType.STEAM_MACOS):
            raise TypeError("SaveGameType")
        
        GameData.__init__(self,
                          sgtype,
                          appid,
                          savegame_root,
                          savegame_dir,
                          variables,
                          file_match,
                          ignore_match)
        self.__installdir = installdir
        
    def get_variables(self):
        vars = super().get_variables()
        vars["INSTALLDIR"] = self.installdir if self.installdir else ""
        
    @Property
    def installdir(self):
        return self.__installdir
    @installdir.setter
    def installdir(self,installdir:str|None):
        self.__installdir = installdir

    def serialize(self):
        ret = super().serialize()
        ret['appid'] = self.appid
        
        if self.installdir:
            ret['installdir'] = self.installdir

        return ret
    
class SteamWindowsGame(SteamGame):
    def __init__(self,
                 appid:int,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 installdir:str|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        SteamGame.__init__(self,
                           SavegameType.STEAM_WINDOWS,
                           appid,
                           savegame_root,
                           savegame_dir,
                           variables,
                           installdir,
                           file_match,
                           ignore_match)
        
class SteamLinuxGame(SteamGame):
    def __init__(self,
                 appid:int,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 installdir:str|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        SteamGame.__init__(self,
                           SavegameType.STEAM_LINUX,
                           appid,
                           savegame_root,
                           savegame_dir,
                           variables,
                           installdir,
                           file_match,
                           ignore_match)

class SteamMacOSGame(SteamGame):
    def __init__(self,
                 appid:int,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 installdir:str|None=None,
                 file_match:list|None=None,
                 ignore_match:list|None=None):
        SteamGame.__init__(self,
                           SavegameType.STEAM_MACOS,
                           appid,
                           savegame_root,
                           savegame_dir,
                           variables,
                           installdir,
                           file_match,
                           ignore_match)

    
class Game(GObject):
    @staticmethod
    def new_from_dict(config:str):
        logger = logger.getChild("Game.new_from_dict()")
        
        def get_file_match(conf:dict):
            conf_fm = conf['file_match'] if 'file_match' in conf else None
            conf_im = conf['ignore_match'] if 'ignore_match' in conf else None
            
            if (conf_fm):
                file_match = []
                for cfm in conf_fm:
                    if ('type' in cfm and 'match' in cfm):
                        try:
                            file_match.append(GameFileMatcher(GameFileType.from_string(cfm['type'],cfm['match'])))
                        except Exception as ex:
                            logger.error("Adding GameFileMatcher to file_match failed! ({})!".format(ex))
                    else:
                        logger.error("Illegal file_match settings! (\"type\" or \"match\" missing!)")
                        
            else:
                file_match = None
                
            if (conf_im):
                ignore_match = []
                for cim in conf_im:
                    if ('type' in cim and 'match' in cim):
                        try:
                            file_match.append(GameFileMatcher(GameFileType.from_string(cim['type'],cim['match'])))
                        except Exception as ex:
                            logger.error("Adding GameFileMatcher to ignore_match failed! ({})!".format(ex))
                    else:
                        logger.error("Illegal ignore_match settings! (\"type\" or \"match\" missing!)")
            else:
                ignore_match = None
                
            return (file_match,ignore_match)
                
        def new_steam_game(conf,cls:SteamGame):
            appid = conf['appid'] if 'appid' in conf else None
            sgroot = conf['savegame_root'] if 'savegame_root' in conf else None
            sgdir = conf['savegame_dir'] if 'savegame_dir' in conf else None
            vars = conf['variables'] if 'variables' in conf else None
            installdir = conf['installdir'] if 'installdir' in conf else None
            file_match,ignore_match = get_file_match(conf)
                
            if appid is not None and sgroot and sgdir:
                cls(appid,sgroot,sgdir,vars,installdir,file_match,ignore_match)
            return None
        # new_steam_game()
        
        if not 'id' in config or not 'name' in config:
            return None
        
        id = config['id']
        name = config['name']
        sgname = config['savegame_name'] if 'savegame_name' in config else id
        sgtype = config['savegame_type'] if 'savegame_type' in config else SavegameType.UNSET
        
        game = Game(id,name,sgname)
        game.savegame_type = sgtype
        game.is_active = config['is_active'] if 'is_active' in config else False
        game.is_live = config['is_live'] if 'is_live' in config else True
        
        if 'windows' in config:
            winconf = config['windows']
            sgroot = winconf['savegame_root'] if 'savegame_root' in winconf else None
            sgdir = winconf['savegame_dir'] if 'savegame_dir' in winconf else None
            vars = winconf['variables'] if 'variables' in winconf else None
            installdir = winconf['installdir'] if 'installdir' in winconf else None
            game_regkeys = winconf['game_registry_keys'] if 'game_registry_keys' in winconf else None
            installdir_regkeys = winconf['installdir_registry_keys'] if 'installdir_registry_keys' in winconf else None
            file_match,ignore_match = get_file_match(winconf)
            if (sgroot and sgdir):
                game.windows = WindowsGame(sgroot,
                                           sgdir,
                                           vars,
                                           installdir,
                                           game_regkeys,
                                           installdir_regkeys,
                                           file_match,
                                           ignore_match)
        
        if 'linux' in config:
            linconf = config['linux']
            sgroot = linconf['savegame_root'] if 'savegame_root' in linconf else None
            sgdir = linconf['savegame_dir'] if 'savegame_dir' in linconf else None
            vars = linconf['variables'] if 'variables' in linconf else None
            binary = linconf['binary'] if 'binary' in linconf else None
            file_match,ignore_match = get_file_match(linconf)
            if (sgroot and sgdir):
                game.linux = LinuxGame(sgroot,sgdir,vars,binary,file_match,ignore_match)
                
        if 'macos' in config:
            macconf = config['macos']
            sgroot = macconf['savegame_root'] if 'savegame_root' in macconf else None
            sgdir = macconf['savegame_dir'] if 'savegame_dir' in macconf else None
            vars = macconf['variables'] if 'variables' in macconf else None
            binary = macconf['binary'] if 'binary' in macconf else None
            file_match,ignore_match = get_file_match(macconf)
            if (sgroot and sgdir):
                game.macos = MacOSGame(sgroot,sgdir,vars,binary,file_match,ignore_match)
        
        if 'steam_windows' in config:
            game.steam_windows = new_steam_game(config['steam_windows'],SteamWindowsGame)
        if 'steam_linux' in config:
            game.steam_linux = new_steam_game(config['steam_linux'],SteamLinuxGame)
        if 'steam_macos' in config:
            game.steam_macos = new_steam_game(config['steam_macos'],SteamMacOSGame)
            
        return game
    
    @staticmethod
    def new_from_json_file(filename:str):
        if not os.path.isfile(filename):
            raise FileNotFoundError("Filename \"{filename}\" not found!".format(filename=filename))
        with open(filename,'rt',encoding="UTF-8") as ifile:
            return Game.new_from_dict(json.loads(ifile.read()))
        
    def __init__(self,id:str,name:str,savegame_name:str):
        GObject.__init__(self)
        self.__id = id
        self.__name = name
        self.__filename = None
        self.__savegame_name = savegame_name
        self.__savegame_type = SavegameType.UNSET
        self.__active = False
        self.__live = True
        
        self.__windows = None
        self.__linux = None
        self.__macos = None
        self.__steam_windows = None
        self.__steam_linux = None
        self.__steam_macos = None
        self.__gog_windows = None
        self.__gog_linux = None
        self.__epic_windows = None
        self.__epic_linux = None
        
    @Property(type=str)
    def id(self)->str:
        return self.__id
    @id.setter
    def id(self,id:str):
        self.__id = id

    
    @Property(type=str)
    def name(self)->str:
        return self.__name
    @name.setter
    def name(self,name:str):
        self.__name = name
        
    @Property(type=str)
    def savegame_name(self)->str:
        return self.__savegame_name
    @savegame_name.setter
    def savegame_name(self,sgname:str):
        self.__savegame_name = sgname
    
    @Property
    def savegame_type(self)->SavegameType:
        return self.__savegame_type
    @savegame_type.setter
    def savegame_type(self,sgtype:SavegameType):
        self.__savegame_type = sgtype
        
    @Property(type=bool,default=False)
    def is_active(self)->bool:
        return self.__active
    @is_active.setter
    def is_active(self,active:bool):
        self.__active = bool(active)
        
    @Property(type=bool,default=True)
    def is_live(self)->bool:
        return self.__live
    @is_live.setter
    def is_live(self,live:bool):
        self.__live = bool(live)

    @Property
    def filename(self)->str|None:
        if not self.__id:
            return None
        
        if not self.__filename:
            GLib.build_filename(settings.gameconf_dir,'.'.join((self.id,'gameconf')))
            
        return self.__filename
    @filename.setter
    def filename(self,fn:str):
        if not os.path.isabs(fn):
            self.__filename = GLib.build_filename(settings.gameconf_dir,fn)
        else:
            self.__filename = fn
    
    @Property
    def game_data(self):
        sgtype = self.savegame_type
        if (sgtype == SavegameType.WINDOWS):
            return self.windows
        elif (sgtype == SavegameType.LINUX):
            return self.linux
        elif (sgtype == SavegameType.MACOS):
            return self.macos
        elif (sgtype == SavegameType.STEAM_WINDOWS):
            return self.steam_windows
        elif (sgtype == SavegameType.STEAM_LINUX):
            return self.steam_linux
        elif (sgtype == SavegameType.STEAM_MACOS):
            return self.steam_macos
        elif (sgtype == SavegameType.GOG_WINDOWS):
            return self.__gog_windows
        elif (sgtype == SavegameType.GOG_LINUX):
            return self.__gog_linux
        elif (sgtype == SavegameType.EPIC_WINDOWS):
            return self.__epic_windows
        elif (sgtype == SavegameType.EPIC_LINUX):
            return self.__epic_linux
        return None
        
    @Property
    def windows(self)->WindowsGame|None:
        return self.__windows
    @windows.setter
    def windows(self,data:WindowsGame|None):
        if not data:
            self.__windows = None
        else:
            if not isinstance(data,WindowsGame):
                raise TypeError("WindowsGame")
            self.__windows = data

    @Property
    def linux(self)->LinuxGame|None:
        return self.__linux
    @linux.setter
    def linux(self,data:LinuxGame):
        if not data:
            self.__linux = None
        else:
            if not isinstance(data,LinuxGame):
                raise TypeError("LinuxGame")
            self.__linux = data
            
    @Property
    def macos(self)->MacOSGame|None:
        return self.__macos
    @macos.setter
    def macos(self,data:MacOSGame|None):
        if not data:
            self.__macos = None
        else:
            if not isinstance(data,MacOSGame):
                raise TypeError("MacOSGame")
            self.__macos = data
    
    @Property
    def steam_windows(self)->SteamWindowsGame|None:
        return self.__steam_windows
    @steam_windows.setter
    def steam_windows(self,data:SteamWindowsGame|None):
        if not data:
            self.__steam_windows = None
        else:
            if not isinstance(data,SteamWindowsGame):
                raise TypeError("SteamWindowsGame")
            self.__steam_windows = data
            
    @Property
    def steam_linux(self)->SteamLinuxGame|None:
        return self.__steam_linux
    @steam_linux.setter
    def steam_windows(self,data:SteamLinuxGame|None):
        if not data:
            self.__steam_linux = None
        else:
            if not isinstance(data,SteamLinuxGame):
                raise TypeError("SteamWindowsGame")
            self.__steam_linux = data
            
    @Property
    def steam_macos(self)->SteamMacOSGame|None:
        return self.__steam_macos
    @steam_macos.setter
    def steam_macos(self,data:SteamMacOSGame|None):
        if not data:
            self.__steam_macos = None
        else:
            if not isinstance(data,SteamMacOSGame):
                raise TypeError("SteamWindowsGame")
            self.__steam_macos = data
            
    def serialize(self)->dict:
        ret = {
            'id': self.id,
            'name': self.name,
            'savegame_name': self.savegame_name,
            'savegame_type': self.savegame_type.value,
            'is_active': self.is_active,
            'is_live': self.is_live,
        }
        
        if (self.windows):
            ret['windows'] = self.windows.serialize()
        if (self.linux):
            ret['linux'] = self.linux.serialize()
        if (self.macos):
            ret['macos'] = self.macos.serialize()
        if (self.steam_windows):
            ret['steam_windows'] = self.steam_windows.serialize()
        if (self.steam_linux):
            ret['steam_linux'] = self.steam_linux.serialize()
        if (self.steam_macos):
            ret['steam_macos'] = self.steam_macos.serialize()
        #if self.gog_windows:
        #    ret['gog_windows'] = self.gog_windows.serialize()
        #if self.gog_linux:
        #    ret['gog_linux'] = self.gog_linux.serialize()
        #if self.epic_windows:
        #    ret['epic_windows'] = self.epic_windows.serialize()
        #if self.epic_linux:
        #    ret['epic_linux'] = self.epic_linux.serialize()
        
        return ret

    def save(self):
        data = self.serialize()
        old_path = pathlib.Path(self.filename).resolve()
        new_path = pathlib.Path(settings.gameconf_dir / '.'.join(self.id,'gameconf')).resolve()
        if (str(old_path) != str(new_path)) and old_path.is_file():
            os.unlink(old_path)
        if not new_path.parent.is_dir():
            os.makedirs(new_path.parent)
            
        with open(new_path,'wt',encoding='UTF-8') as ofile:
            ofile.write(json.dumps(self.serialize(),ensure_ascii=False,indent=4))
        
GAMES={}
STEAM_GAMES={}
STEAM_LINUX_GAMES={}
STEAM_WINDOWS_GAMES={}
STEAM_MACOS_GAMES={}

def __init_games():
    gameconf_dir = settings.gameconf_dir
    if not os.path.isdir(gameconf_dir):
        return
    
    for gcf in (os.path.join(gameconf_dir,i) for i in os.path.listdir(gameconf_dir)):
        if not os.path.isfile(gcf) or not gcf.endswith('.gameconf'):
            continue
            
        try:
            game = Game.new_from_json_file(gcf)
            if not game:
                continue
        except:
            continue
        
        GAMES[game.id] = game
        if (game.steam_windows):
            if not game.steam_windows.appid in STEAM_GAMES:
                STEAM_GAMES[game.steam_windows.appid] = game
            STEAM_WINDOWS_GAMES[game.steam_windows.appid] = game
        if (game.steam_linux):
            if not game.steam_linux.appid in STEAM_GAMES:
                STEAM_GAMES[game.steam_linux.appid] = game
            STEAM_LINUX_GAMES[game.steam_linux.appid] = game
        if (game.steam_macos):
            if not game.steam_macos.appid in STEAM_GAMES:
                STEAM_GAMES[game.steam_macos.appid] = game
            STEAM_MACOS_GAMES[game.steam_macos.appid] = game
__init_games()

def add_game(game:Game):
    GAMES[game.id] = game
    if game.steam_windows:
        if not game.steam_windows.appid in STEAM_GAMES:
            STEAM_GAMES[game.steam_windows.appid] = game
        STEAM_WINDOWS_GAMES[game.steam_windows.appid] = game
    if (game.steam_linux):
        if not game.steam_linux.appid in STEAM_GAMES:
            STEAM_GAMES[game.steam_linux.appid] = game
        STEAM_LINUX_GAMES[game.steam_linux.appid] = game
    if (game.steam_macos):
        if not game.steam_macos.appid in STEAM_GAMES:
            STEAM_GAMES[game.steam_macos.appid] = game
        STEAM_MACOS_GAMES[game.steam_macos.appid] = game