###############################################################################
# sgbackup - The SaveGame Backup tool                                         #
#    Copyright (C) 2024,2025  Christian Moser                                      #
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

from . import _import_gtk

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
import datetime
from string import Template

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
    """
    SavegameType The savegame type for `Game` instance.
    
    The SavegameType selects the `GameData` provider for the 
    `Game` instance.
    """
    
    #: UNSET The SavegameType is unset
    UNSET = "unset"
    
    #: OTHER Not listed game-provider.
    #:
    #: **Currently not supported!**
    OTHER = "other"
    
    #: WINDOWS Native Windows game
    WINDOWS = "windows"
    
    #: LINUX Native Linux game
    LINUX = "linux"
    
    #: MACOS Native MacOS game
    MACOS = "macos"
    
    #: STEAM_WINDOWS *Steam* for Windows
    STEAM_WINDOWS = "steam_windows"
    
    #: STEAM_LINUX *Steam* for Linux
    STEAM_LINUX = "steam_linux"
    
    #: STEAM_MACOS *Steam* for MacOS
    STEAM_MACOS = "steam_macos"
    
    #: GOG WINDOWS *Good old Games* for Windows
    #:
    #: **Currently not supported!**
    GOG_WINDOWS = "gog_windows"
    
    #: GOG_LINUX *Good old Games* for Linux
    #:
    #: **Currently not supported!**
    GOG_LINUX = "gog_linux"
    
    #: EPIC_WINDOWS *Epic Games* for Windows
    #:
    #: **Currently not supported!**
    EPIC_WINDOWS = "epic_windows"
    
    #: EPIC_LINUX *Epic Games* for Linux
    #:
    #: **Currently not supported!**
    EPIC_LINUX = "epic_linux"
    
    @staticmethod
    def from_string(typestring:str):
        """
        from_string Get SavegameType from string.

        :param typestring: The string to parse
        :type typestring: str
        :return: The SavegameType if any. If no matching SavegameType is found,
            SavegameType.UNSET is returned.
        :rtype: SavegameType
        """
        
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
        elif (s == 'steam_windows' or s == 'steam-windows' or s == 'steamwindows' or s == 'steam.windows'):
            return st.STEAM_WINDOWS
        elif (s == 'steam_linux' or  s == 'steam-linux' or s == 'steamlinux' or s == 'steam.linux'):
            return st.STEAM_LINUX
        elif (s == 'steam_macos' or s == 'steam-macos' or s == 'steammacos' or s == 'steam.macos'):
            return st.STEAM_MACOS
        elif (s == 'gog_winows' or s == 'gog-windows' or s == 'gogwindows' or s == 'gog.windows'):
            return st.GOG_WINDOWS
        elif (s == 'gog_linux' or s == 'gog-linux' or s == 'goglinux' or s == 'gog.linux'):
            return st.GOG_LINUX
        elif (s == 'epic_windows' or s == 'epic-windows' or s == 'epicwindows' or s == 'epic.windows'):
            return st.EPIC_WINDOWS
        elif (s == 'epic_linux' or s == 'epic-linux' or s == 'epiclinux' or s == 'epic.linux'):
            return st.EPIC_LINUX
        
        return st.UNSET
    
    
VALID_SAVEGAME_TYPES = [
    SavegameType.WINDOWS,
    SavegameType.LINUX,
    SavegameType.MACOS,
    SavegameType.STEAM_LINUX,
    SavegameType.STEAM_MACOS,
    SavegameType.STEAM_WINDOWS,
    #SavegameType.EPIC_LINUX,
    SavegameType.EPIC_WINDOWS,
    #SavegameType.GOG_LINUX,
    #SavegameType.GOG_WINDOWS,
]

SAVEGAME_TYPE_ICONS = {
    SavegameType.UNSET : None,
    SavegameType.WINDOWS: 'windows-svgrepo-com-symbolic',
    SavegameType.LINUX: 'linux-svgrepo-com-symbolic',
    SavegameType.MACOS: 'apple-svgrepo-com-symbolic',
    SavegameType.STEAM_LINUX: 'steam-svgrepo-com-symbolic',
    SavegameType.STEAM_MACOS: 'steam-svgrepo-com-symbolic',
    SavegameType.STEAM_WINDOWS: 'steam-svgrepo-com-symbolic',
    SavegameType.EPIC_LINUX: 'epic-games-svgrepo-com-symbolic',
    SavegameType.EPIC_WINDOWS: 'epic-games-svgrepo-com-symbolic',
    SavegameType.GOG_LINUX: 'gog-com-svgrepo-com-symbolic',
    SavegameType.GOG_WINDOWS: 'gog-com-svgrepo-com-symbolic',
}    

class GameProvider(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    STEAM = "steam"
    EPIC_GAMES = "epic-games"
    GOG = "gog"
    
GAME_PROVIDER_ICONS = {
    GameProvider.WINDOWS: 'windows-svgrepo-com-symbolic',
    GameProvider.LINUX: 'liux-svgrepo-com-symbolic',
    GameProvider.MACOS: 'apple-svgrepo-com-symbolic',
    GameProvider.STEAM: 'steam-svgrepo-com-symbolic',
    GameProvider.EPIC_GAMES: 'epic-games-svgrepo-com-symbolic',
    GameProvider.GOG: 'gog-com-svgrepo-com-symbolic',
}

class GameFileType(StrEnum):
    """
    GameFileType The file matcher type for `GameFileMatcher`.
    
    The path to be matched is originating from *${SAVEGAME_ROOT}/${SAVEGAME_DIR}*. 
    """
    
    #: GLOB Glob matching.
    GLOB = "glob"
    
    #: REGEX Regex file matching
    REGEX = "regex"
    
    #: FILENAME Filename matching.
    FILENAME = "filename"
    
    @staticmethod
    def from_string(typestring:str):
        """
        from_string Get the `GameFileType` from a string.

        If an illegal string-value is given this method raises a `ValueError`.
        
        :param typestring: The string to be used.
        :type typestring: str
        :raises ValueError: If an illegal string is given.
        :return: The corresponding Enum-value
        :rtype: GameFileType
        """
        s = typestring.lower()
        if (s == 'glob'):
            return GameFileType.GLOB
        elif (s == 'regex'):
            return GameFileType.REGEX
        elif (s == 'filename'):
            return GameFileType.FILENAME
        
        raise ValueError("Unknown GameFileType \"{}\"!".format(typestring))

class GameFileMatcher(GObject):
    """
    GameFileMatcher Match savegame files if they are  to be included in the backup.
    """
    __gtype_name__ = "GameFileMatcher"
    
    def __init__(self,match_type:GameFileType,match_file:str):
        GObject.__init__(self)
        self.match_type = match_type
        self.match_file = match_file
    
    @Property
    def match_type(self)->GameFileType:
        """
        match_type The type of the matcher.
        
        :type: GameFileType
        """
        
        return self.__match_type
    
    @match_type.setter
    def match_type(self,match_type:GameFileType):
        if not isinstance(match_type,GameFileType):
            raise TypeError("match_type is not a GameFileType instance!")
        self.__match_type = match_type
        
    @Property(type=str)
    def match_file(self)->str:
        """
        match_file The matcher value.
        
        :type: str
        """
        return str(self.__match_file)
    
    @match_file.setter
    def match_file(self,file:str):
        self.__match_file = file    
    
    def match(self,rel_filename:str)->bool:
        """
        match Match the file.

        :param rel_filename: The relative filename originating from 
            *${SAVEGAME_ROOT}/${SAVEGAME_DIR}*.
        :type rel_filename: str
        :rtype: bool
        :returns: True if file matches
        """
        def match_glob(filename)->bool:
            return fnmatch.fnmatch(filename,self.__match_file)
        # match_glob()
        
        def match_filename(filename):
            if (self.match_file.endswith('/')):
                if filename == self.match_file[:-1] or filename.startswith(self.match_file):
                    return True
            elif filename == self.match_file:
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
    __gtype_name__ = 'GameData'
    
    """
    :class: GameData Base class for savegame specific data data.
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
        self.file_matchers = file_match
        self.ignore_matchers = ignore_match
        
        if variables is not None:
            variables.update(variables)
            
                        
    @Property
    def savegame_type(self)->SavegameType:
        """
        :type: SavegameType
        """
        return self.__savegame_type
    
    @Property(type=str)
    def savegame_root(self)->str:
        """
        :type: str
        """
        return self.__savegame_root
    
    @savegame_root.setter
    def savegame_root(self,sgroot:str):
        self.__savegame_root = sgroot
    
    @Property
    def savegame_dir(self)->str:
        """
        :type: str
        """
        return self.__savegame_dir
    
    @savegame_dir.setter
    def savegame_dir(self,sgdir:str):
        self.__savegame_dir = sgdir
        
    @Property
    def variables(self)->dict[str:str]:
        """
        :type: dict[str:str]
        """
        return self.__variables
    @variables.setter
    def variables(self,vars:dict|None):
        if not vars:
            self.__variables = {}
        else:
            self.__variables = dict(vars)
    
    @Property
    def file_matchers(self)->list[GameFileMatcher]:
        """
        :type: list[GameFileMatcher]
        """
        return self.__filematchers
    
    @file_matchers.setter
    def file_matchers(self,fm:list[GameFileMatcher]|None):
        self.__filematchers = []
        if fm:
            for matcher in fm:
                if not isinstance(matcher,GameFileMatcher):
                    raise TypeError("\"file_match\" needs to be \"None\" or a list of \"GameFileMatcher\" instances!")
            self.__filematchers = list(fm)
            
    
    @Property
    def ignore_matchers(self)->list[GameFileMatcher]:
        """
        :type: list[GameFileMatcher]
        """
        return self.__ignorematchers
    
    @ignore_matchers.setter
    def ignore_matchers(self,im:list[GameFileMatcher]|None):
        self.__ignorematchers = []
        if im:
            for matcher in im:
                if not isinstance(matcher,GameFileMatcher):
                    raise TypeError("\"ignore_match\" needs to be \"None\" or a list of \"GameFileMatcher\" instances!")
            self.__ignorematchers = list(im)
            
    @Property(type=bool,default=False)
    def is_valid(self)->bool:
        return (bool(self.__savegame_root) and bool(self.__savegame_dir) and (self.__savegame_type != SavegameType.UNSET))
    
    
    def has_variable(self,name:str)->bool:
        """
        has_variable Check if variable exists.

        :param name: The variable name.
        :type name: str
        :return: `True` if the variable exists.
        :rtype: bool
        """
        
        return (name in self.__variables)
    
    def get_variable(self,name:str)->str:
        """
        get_variable Get a variable value byy variable name.

        :param name: The variable name
        :type name: str
        :return: The vairable value if the variable exists or an empty string.
        :rtype: str
        """
        if name not in self.__variables:
            return ""
        return self.__variables[name]
        
    def set_variable(self,name:str,value:str):
        """
        set_variable Set a variable.
        
        If the variable exists, it is replaced by the new variable.

        :param name: The variable name.
        :type name: str
        :param value: The variable value.
        :type value: str
        """
        self.__variables[name] = value
        
    def delete_variable(self,name:str):
        """
        delete_variable Deletes as variable if the variable exists

        :param name: The vairable name to delete.
        :type name: str
        """
        if name in self.__variables:
            del self.__variables[name]
    
    def get_variables(self)->dict[str:str]:
        """
        get_variables Get the variables set by this instance.

        :return: The variables as a dict.
        :rtype: dict[str:str]
        """
        return dict(self.variables)
    
    def match_file(self,rel_filename:str)->bool:
        """
        match_file Matches a file with the `GameFileMatcher`s for this class.
        
        This method returns `True` if there is no `GameFileMatcher` set for 
        `GameData.file_match`.

        :param rel_filename: The relative filename originating from *$SAVEGAME_DIR*
        :type rel_filename: str
        :return: `True` if the file matches.
        :rtype: bool
        """
        if not self.file_matchers:
            return True
        
        for fm in self.file_matchers:
            if fm.match(rel_filename):
                return True
        return False
            
        
    def match_ignore(self,rel_filename:str)->bool:
        """
        match_ignore Matches file agains the ignore_match `GameFileMatcher`s.
        
        This method returns `False` if there is no `GameFileMatcher` set in 
        `GameData.ignore_match`.

        :param rel_filename: The relative filename originating from *$SAVEGAME_DIR*
        :type rel_filename: str
        :return: `True` if the file matches.
        :rtype: bool
        """
        if not self.ignore_matchers:
            return False
        
        for fm in self.ignore_matchers:
            if fm.match(rel_filename):
                return True
        return False
    
    def match(self,rel_filename:str)->bool:
        """
        match Match files against `file_match` and `ignore_match`.
        
        If this method returns `True` the file should be included in the
        savegame backup.

        :param rel_filename: The relative filename originating from *$SAVEGAME_DIR*
        :type rel_filename: str
        :return: True if the file should be included in the savegame backup.
        :rtype: bool
        """
        if self.match_file(rel_filename) and not self.match_ignore(rel_filename):
            return True
        return False
    
    def add_file_match(self,matcher:GameFileMatcher):
        """
        add_file_match Add a `GameFileMatcher` to `file_match`.

        :param matcher: The `GameFileMatcher` to add.
        :type matcher: GameFileMatcher
        :raises TypeError: If the `matcher` is not a `GameFileMatcher` instance.
        """
        if not isinstance(matcher,GameFileMatcher):
            raise TypeError("matcher is not a \"GameFileMatcher\" instance!")
        self.__filematchers.append(matcher)
        
    def remove_file_match(self,matcher:GameFileMatcher):
        """
        remove_file_match Remove a file_matcher.

        :param matcher: The `GameFileMatcher` to remove.
        :type matcher: GameFileMatcher
        """
        for i in reversed(range(len(self.__filematchers))):
            if (matcher == self.__filematchers[i]):
                del self.__filematchers[i]
    
    def add_ignore_match(self,matcher:GameFileMatcher):
        """
        add_file_match Add a `GameFileMatcher` to `ignore_match`.

        :param matcher: The `GameFileMatcher` to add.
        :type matcher: GameFileMatcher
        :raises TypeError: If the `matcher` is not a `GameFileMatcher` instance.
        """
        if not isinstance(matcher,GameFileMatcher):
            raise TypeError("matcher is not a \"GameFileMatcher\" instance!")
        self.__ignorematchers.append(matcher)
        
    def remove_ignore_match(self,matcher:GameFileMatcher):
        """
        remove_file_match Remove a ignore_match.

        :param matcher: The `GameFileMatcher` to remove.
        :type matcher: GameFileMatcher
        """

        for i in reversed(range(len(self.__ignorematchers))):
            if (matcher == self.__ignorematchers[i]):
                del self.__ignorematchers[i]
                
    def serialize(self)->dict:
        """
        serialize Serialize the instance to a dict.
        
        This method should be overloaded by child-classes, so that their data
        is exported too.

        :return: The dict holding the data for recreating an instance of this class.
        :rtype: dict
        """
        ret = {
            'savegame_root': self.savegame_root,
            'savegame_dir': self.savegame_dir,
        }
        if (self.__variables):
            ret['variables'] = self.variables
        if (self.file_matchers):
            fm = []
            for matcher in self.file_matchers:
                fm.append({'type':matcher.match_type.value,'match':matcher.match_file})
            ret['file_match'] = fm
                
        if (self.ignore_matchers):
            im = []
            for matcher in self.ignore_matchers:
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
    
    @game_registry_keys.setter
    def game_registry_keys(self,keys:list[str]|tuple[str]|None):
        self.__game_registry_keys = []
        if keys:
            for rk in keys:
                self.__game_registry_keys.append(str(rk))
    
    @Property
    def installdir_registry_keys(self)->list:
        return self.__installdir_registry_keys
    
    @installdir_registry_keys.setter
    def installdir_registry_keys(self,keys:list[str]|tuple[str]|None):
        self.__installdir_registry_keys = []
        if keys:
            for rk in keys:
                self.__installdir_registry_keys.append(str(rk))
                
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
        return variables
        
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
                          savegame_root,
                          savegame_dir,
                          variables,
                          file_match,
                          ignore_match)
        self.appid = int(appid)
        self.installdir = installdir
        self.librarydir=None
        
    def get_variables(self):
        vars = super().get_variables()
        vars["INSTALLDIR"] = self.installdir if self.installdir else ""
        vars["STEAM_APPID"] = str(self.appid)
        vars["STEAM_LIBDIR"] = self.librarydir if self.librarydir else ""
        vars["STEAM_LIBRARY_DIR"] = self.librarydir if self.librarydir else ""
        vars["STEAM_COMPATDATA"] = self.compatdata if self.compatdata else ""
        
        return vars
        
    @Property(type=int)
    def appid(self):
        return self.__appid
    @appid.setter
    def appid(self,appid):
        self.__appid = appid
        
    @Property
    def installdir(self):
        return self.__installdir
    @installdir.setter
    def installdir(self,installdir:str|None):
        self.__installdir = installdir

    @Property
    def librarydir(self)->str|None:
        if not self.__librarydir and self.installdir:
            return str(pathlib.Path(self.installdir).resolve().parent.parent.parent)
        return self.__librarydir
    
    @librarydir.setter
    def librarydir(self,directory):
        if not directory:
            self.__librarydir = None
        elif not os.path.isdir(directory):
            raise ValueError("Steam librarydir is not a valid directory!")
        self.__librarydir = directory
    
    @Property
    def compatdata(self)->str|None:
        libdir = self.librarydir
        if libdir:
            return str(pathlib.Path(libdir).resolve() / 'steamapps' / 'compatdata')
        return None
    
    def serialize(self):
        ret = super().serialize()
        ret['appid'] = self.appid
        
        if self.installdir:
            ret['installdir'] = str(self.installdir) if self.installdir else ""
            ret['librarydir'] = str(self.librarydir) if self.librarydir else ""

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

class SteamPlatformData(GameData):
    def __init__(self,
                 savegame_type:SavegameType,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 file_match:str|None=None,
                 ignore_match:str|None=None,
                 installdir:str|None=None,
                 librarydir:str|None=None):
        
        if savegame_type not in (SavegameType.STEAM_WINDOWS,
                                 SavegameType.STEAM_LINUX,
                                 SavegameType.STEAM_MACOS):
            raise TypeError("\"savegame_type\" is not valid!")
        
        GameData.__init__(self,
                          savegame_type=savegame_type,
                          savegame_root=savegame_root,
                          savegame_dir=savegame_dir,
                          variables=variables,
                          file_match=file_match,
                          ignore_match=ignore_match)
        self.installdir = installdir
        self.librarydir = librarydir
            
    @Property(type=str)
    def installdir(self)->str:
        return self.__installdir if self.__installdir else ""
    
    @installdir.setter
    def installdir(self,installdir:str|None):
        self.__installdir = installdir


    @Property(type=str)
    def librarydir(self)->str:
        return self.__librarydir if self.__librarydir else ""
    
    @librarydir.setter
    def librarydir(self,steam_libdir:str|None):
        self.__librarydir = steam_libdir

    def serialize(self)->dict:
        data = super().serialize()
        if self.__installdir:
            data['installdir'] = self.__installdir
        if self.__librarydir:
            data['librarydir'] = self.__librarydir
        
        return data
    
class SteamWindowsData(SteamPlatformData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 file_match:str|None=None,
                 ignore_match:str|None=None,
                 installdir:str|None=None,
                 librarydir:str|None=None):
        SteamPlatformData.__init__(self,
                                   savegame_type=SavegameType.STEAM_WINDOWS,
                                   savegame_root=savegame_root,
                                   savegame_dir=savegame_dir,
                                   variables=variables,
                                   file_match=file_match,
                                   ignore_match=ignore_match,
                                   installdir=installdir,
                                   librarydir=librarydir)

class SteamLinuxData(SteamPlatformData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 file_match:str|None=None,
                 ignore_match:str|None=None,
                 installdir:str|None=None,
                 librarydir:str|None=None):
        SteamPlatformData.__init__(self,
                                   savegame_type=SavegameType.STEAM_LINUX,
                                   savegame_root=savegame_root,
                                   savegame_dir=savegame_dir,
                                   variables=variables,
                                   file_match=file_match,
                                   ignore_match=ignore_match,
                                   installdir=installdir,
                                   librarydir=librarydir)

class SteamMacOSData(SteamPlatformData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict|None=None,
                 file_match:str|None=None,
                 ignore_match:str|None=None,
                 installdir:str|None=None,
                 librarydir:str|None=None):
        SteamPlatformData.__init__(self,
                                   savegame_type=SavegameType.STEAM_MACOS,
                                   savegame_root=savegame_root,
                                   savegame_dir=savegame_dir,
                                   variables=variables,
                                   file_match=file_match,
                                   ignore_match=ignore_match,
                                   installdir=installdir,
                                   librarydir=librarydir)


class SteamGameData(GObject):
    def __init__(self,appid:int,
                 windows:SteamWindowsData|None=None,
                 linux:SteamLinuxData|None=None,
                 macos:SteamMacOSData|None=None):
        GObject.__init__(self)
        self.__appid = int(appid)
        self.windows = windows
        self.linux = linux
        self.macos = macos
        
    @Property(type=int)
    def appid(self)->int:
        return self.__appid
    
    @appid.setter
    def appid(self,appid:int):
        return self.__appid
    
    @property
    def windows(self)->SteamWindowsData|None:
        return self.__windows_data
        
    @windows.setter
    def windows(self,data:SteamWindowsData|None):
        self.__windows_data = data
        
    @property
    def linux(self)->SteamLinuxData|None:
        return self.__linux_data
    
    @linux.setter
    def linux(self,data:SteamLinuxData|None):
        self.__linux_data = data
        
    @property
    def macos(self)->SteamMacOSData|None:
        return self.__macos_data
    
    @macos.setter
    def macos(self,data:SteamMacOSData|None):
        self.__macos_data = data
        
    @property
    def windows_game(self)->SteamWindowsGame|None:
        if self.windows:
            return SteamWindowsGame(appid=self.appid,
                                    savegame_root=self.windows.savegame_root,
                                    savegame_dir=self.windows.savegame_dir,
                                    variables=self.windows.variables,
                                    installdir=self.windows.installdir,
                                    file_match=self.windows.file_matchers,
                                    ignore_match=self.windows.ignore_matchers)
        return None
    
    @property
    def linux_game(self)->SteamLinuxGame|None:
        if self.linux:
            return SteamLinuxGame(appid=self.appid,
                                  savegame_root=self.linux.savegame_root,
                                  savegame_dir=self.linux.savegame_dir,
                                  variables=self.linux.variables,
                                  installdir=self.linux.installdir,
                                  file_match=self.linux.file_matchers,
                                  ignore_match=self.linux.ignore_matchers)
        return None
    
    @property
    def macos_game(self)->SteamLinuxGame|None:
        if self.macos:
            return SteamMacOSGame(appid=self.appid,
                                  savegame_root=self.macos.savegame_root,
                                  savegame_dir=self.macos.savegame_dir,
                                  variables=self.macos.variables,
                                  installdir=self.macos.installdir,
                                  file_match=self.macos.file_matchers,
                                  ignore_match=self.macos.ignore_matchers)
        return None
    
    def serialize(self)->dict:
        data = {
            'appid': self.appid,
        }
        if self.windows:
            data['windows'] = self.windows.serialize()
        if self.linux:
            data['linux'] = self.linux.serialize()
        if self.macos:
            data['macos'] = self.macos.serialize()
            
        return data


class EpicPlatformData(GameData):
    def __init__(self,
                 savegame_type:SavegameType,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict[str:str],
                 file_match:list[GameFileMatcher],
                 ignore_match:list[GameFileMatcher],
                 installdir:str|None):
        if savegame_type not in (SavegameType.EPIC_WINDOWS,SavegameType.EPIC_LINUX):
            raise ValueError("Savegame type needs to be EPIC_WINDOWS or EPIC_LINUX!")
        
        GameData.__init__(self,
                          savegame_type=savegame_type,
                          savegame_root=savegame_root,
                          savegame_dir=savegame_dir,
                          variables=variables,
                          file_match=file_match,
                          ignore_match=ignore_match)
        
        self.__installdir=installdir
        
    @Property
    def installdir(self)->str:
        return self.__installdir if self.__installdir else ""
    
    @installdir.setter
    def installdir(self,directory:str|None):
        self.__installdir = directory
        
    def serialize(self):
        data = super().serialize()
        if self.__installdir:
            data['installdir'] = self.__installdir
        return data
        
class EpicWindowsData(EpicPlatformData):
    def __init__(self,
                 savegame_root:str,
                 savegame_dir:str,
                 variables:dict[str:str]|None=None,
                 file_match:list[GameFileMatcher]|None=None,
                 ignore_match:list[GameFileMatcher]|None=None,
                 installdir:str|None=None):
        EpicPlatformData.__init__(self,
                          savegame_type=SavegameType.EPIC_WINDOWS,
                          savegame_root=savegame_root,
                          savegame_dir=savegame_dir,
                          variables=variables,
                          file_match=file_match,
                          ignore_match=ignore_match,
                          installdir=installdir)


class EpicGameData(GObject):
    def __init__(self,
                 catalog_item_id:str|None=None,
                 windows:EpicWindowsData|None=None):
        GObject.__init__(self)
        self.__catalog_item_id = catalog_item_id
        self.windows = windows
        
        
    @Property(type=str)
    def catalog_item_id(self)->str:
        return self.__catalog_item_id if self.__catalog_item_id else ""
    
    @catalog_item_id.setter
    def catalog_item_id(self,catalog_item_id:str):
        self.__catalog_item_id = catalog_item_id
        
    @Property
    def windows(self)->EpicWindowsData|None:
        return self.__windows
    
    @windows.setter
    def windows(self,data:EpicWindowsData|None):
        self.__windows = data
        
    @Property(type=bool,default=False)
    def is_valid(self)->bool:
        if (self.windows and self.windows.is_valid):
            return True
        
    def serialize(self):
        ret = {
            "catalog_item_id": self.catalog_item_id
        }
        if self.windows and self.windows.is_valid:
            ret["windows"] = self.windows.serialize()
            
        return ret
    
class Game(GObject):
    __gtype_name__ = "Game"
    
    @staticmethod
    def new_from_dict(config:str):
        _logger = logger.getChild("Game.new_from_dict()")
        
        def get_file_match(conf:dict):
            conf_fm = conf['file_match'] if 'file_match' in conf else []
            conf_im = conf['ignore_match'] if 'ignore_match' in conf else []
            
            if (conf_fm):
                file_match = []
                for cfm in conf_fm:
                    if ('type' in cfm and 'match' in cfm):
                        try:
                            file_match.append(GameFileMatcher(GameFileType.from_string(cfm['type']),cfm['match']))
                        except Exception as ex:
                            _logger.error("Adding GameFileMatcher to file_match failed! ({})!".format(ex))
                    else:
                        _logger.error("Illegal file_match settings! (\"type\" or \"match\" missing!)")
                        
            else:
                file_match = None
                
            if (conf_im):
                ignore_match = []
                for cim in conf_im:
                    if ('type' in cim and 'match' in cim):
                        try:
                            ignore_match.append(GameFileMatcher(GameFileType.from_string(cim['type']),cim['match']))
                        except Exception as ex:
                            _logger.error("Adding GameFileMatcher to ignore_match failed! ({})!".format(ex))
                    else:
                        _logger.error("Illegal ignore_match settings! (\"type\" or \"match\" missing!)")
            else:
                ignore_match = None
                
            return (file_match,ignore_match)
                
        def new_steamdata(conf)->SteamGameData|None:
            def new_steam_platform_data(data:dict,cls:SteamPlatformData)->SteamPlatformData|None:
                if not 'savegame_root' in data or not 'savegame_dir' in data:
                    return None
                
                file_match,ignore_match = get_file_match(data)
                return cls(
                    savegame_root=data['savegame_root'],
                    savegame_dir=data['savegame_dir'],
                    variables=dict(((v['name'],v['value']) for v in data['variables'])) if ('variables' in data and config['variables']) else None,
                    file_match=file_match if 'file_match' in data else None,
                    ignore_match=ignore_match if 'ignore_match' in data else None,
                    installdir=data['installdir'] if ('installdir' in data and data['installdir']) else None,
                    librarydir=data['librarydir'] if ('librarydir' in data and data['librarydir']) else None                   
                )
            
            if ('steam' not in conf):
                return None
            
            steam=conf['steam']
            
            if 'windows' in steam:
                windows = new_steam_platform_data(steam['windows'],SteamWindowsData)
            else:
                windows = None
                
            if 'linux' in steam:
                linux = new_steam_platform_data(steam['linux'],SteamLinuxData)
            else:
                linux = None
                
            if 'macos' in steam:
                macos = new_steam_platform_data(steam['macos'],SteamMacOSData)
            else:
                macos = None
                
            if windows is None and linux is None and macos is None:
                return None
            
            return SteamGameData(steam['appid'] if 'appid' in steam else -1,
                                 windows=windows,
                                 linux=linux,
                                 macos=macos)
        # new_steamdata()

        def new_epic_data(conf:dict):
            def new_epic_platform_data(data,cls):
                if not 'savegame_root' in data or not 'savegame_dir' in data:
                    return None
                
                file_match,ignore_match = get_file_match(data)
                return cls(
                    savegame_root=data['savegame_root'],
                    savegame_dir=data['savegame_dir'],
                    variables=dict(((v['name'],v['value']) for v in data['variables'])) if ('variables' in data and config['variables']) else None,
                    file_match=file_match if 'file_match' in data else None ,
                    ignore_match=ignore_match if 'ignore_match' in data else None,
                    installdir=data['installdir'] if ('installdir' in data and data['installdir']) else None
                )
            
            if not "epic" in conf:
                return None
            
            if ("windows" in conf['epic']):
                windows = new_epic_platform_data(conf['windows'],EpicWindowsData)
            else:
                windows = None
                
            return EpicGameData(conf['epic']['catalog_item_id'] if 'catalog_item_id' in conf['epic'] else "",
                                windows=windows)
            
        # new_epic_data()
            
        if not 'key' in config or not 'name' in config:
            return None
        
        dbid = config['dbid'] if 'dbid' in config else None
        key = config['key']
        name = config['name']
        sgname = config['savegame_name'] if 'savegame_name' in config else key
        sgtype = SavegameType.from_string(config['savegame_type']) if 'savegame_type' in config else SavegameType.UNSET
        
        game = Game(key,name,sgname)
        if dbid:
            game.dbid = dbid
            
        game.savegame_type = sgtype
        game.is_active = config['is_active'] if 'is_active' in config else False
        game.is_live = config['is_live'] if 'is_live' in config else True
        
        if 'windows' in config:
            winconf = config['windows']
            sgroot = winconf['savegame_root'] if 'savegame_root' in winconf else None
            sgdir = winconf['savegame_dir'] if 'savegame_dir' in winconf else None
            vars = winconf['variables'] if 'variables' in winconf else {}
            installdir = winconf['installdir'] if 'installdir' in winconf else None
            game_regkeys = winconf['game_registry_keys'] if 'game_registry_keys' in winconf else []
            installdir_regkeys = winconf['installdir_registry_keys'] if 'installdir_registry_keys' in winconf else []
            file_match,ignore_match = get_file_match(winconf)
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
            vars = linconf['variables'] if 'variables' in linconf else {}
            binary = linconf['binary'] if 'binary' in linconf else None
            file_match,ignore_match = get_file_match(linconf)
            game.linux = LinuxGame(sgroot,sgdir,vars,binary,file_match,ignore_match)
                
        if 'macos' in config:
            macconf = config['macos']
            sgroot = macconf['savegame_root'] if 'savegame_root' in macconf else None
            sgdir = macconf['savegame_dir'] if 'savegame_dir' in macconf else None
            vars = macconf['variables'] if 'variables' in macconf else {}
            binary = macconf['binary'] if 'binary' in macconf else None
            file_match,ignore_match = get_file_match(macconf)
            game.macos = MacOSGame(sgroot,sgdir,vars,binary,file_match,ignore_match)
        
        game.steam = new_steamdata(config)
        game.epic = new_epic_data(config)
            
        return game
    
    @staticmethod
    def new_from_json_file(filename:str):
        if not os.path.isfile(filename):
            raise FileNotFoundError("Filename \"{filename}\" not found!".format(filename=filename))
        with open(filename,'rt',encoding="UTF-8") as ifile:
            x=json.loads(ifile.read())
            game = Game.new_from_dict(x)
            
        if game is not None:
            game.filename = filename
        return game
        
    def __init__(self,key:str,name:str,savegame_name:str):
        GObject.__init__(self)
        self.__dbid = None
        self.__key = key
        self.__name = name
        self.__filename = None
        self.__savegame_name = savegame_name
        self.__savegame_type = SavegameType.UNSET
        self.__active = False
        self.__live = True
        self.__variables = dict()
        
        self.__windows = None
        self.__linux = None
        self.__macos = None
        self.__steam = None
        self.__epic = None
        self.__gog = None
        self.__epic = None
        
    @Property(type=str)
    def dbid(self)->str:
        return self.__dbid
    @dbid.setter
    def dbid(self,id:str):
        self.__dbid = id

    @Property(type=str)
    def key(self)->str:
        return self.__key
    @key.setter
    def key(self,key:str):
        if self.__key and self.__key != key:
            self._old_key = self.__key
        self.__key = key
    
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
        if not self.__filename:
            if not self.key:
                return None
            return os.path.join(settings.gameconf_dir,'.'.join((self.key,'gameconf')))
            
        return self.__filename
    
    @filename.setter
    def filename(self,fn:str):
        if self.__filename and fn != self.__filename and os.path.isfile(self.__filename):
            self.__old_filename = self.__filename
            
        if not os.path.isabs(fn):
            self.__filename = os.path.join(settings.gameconf_dir,fn)
        else:
            self.__filename = fn
    
    @Property
    def variables(self):
        return self.__variables
    @variables.setter
    def variables(self,vars:dict|None):
        if not vars:
            self.__variables = {}
        else:
            self.__variables = dict(vars)
            
    @Property(type=str)
    def subdir(self):
        if self.is_live:
            return "live"
        else:
            return "finished"
        
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
            if self.steam:
                return self.steam.windows_game
        elif (sgtype == SavegameType.STEAM_LINUX):
            if self.steam:
                return self.steam.linux_game
        elif (sgtype == SavegameType.STEAM_MACOS):
            if self.steam:
                return self.steam.macos_game
        #elif (sgtype == SavegameType.GOG_WINDOWS):
        #    return self.__gog_windows
        #elif (sgtype == SavegameType.GOG_LINUX):
        #    return self.__gog_linux
        elif (sgtype == SavegameType.EPIC_WINDOWS):
            if self.epic:
                return self.__epic.windows
        elif (sgtype == SavegameType.EPIC_LINUX):
            return None
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
    def steam(self)->SteamGameData|None:
        return self.__steam
    
    @steam.setter
    def steam(self,steam_data:SteamGameData|None):
        if (not steam_data):
            self.__steam = steam_data
            return
        
        if (not isinstance(steam_data,SteamGameData)):
            raise TypeError("\"steam\" is not \"None\" or a \"SteamGameData\" instance!")
        
        self.__steam = steam_data
        
    @Property
    def steam_windows(self)->SteamWindowsGame|None:
        if self.steam:
            return self.steam.windows_game
        return None
    
    @Property
    def steam_linux(self)->SteamLinuxGame|None:
        if self.steam:
            return self.steam.linux_game
        return None
    
            
    @Property
    def steam_macos(self)->SteamMacOSGame|None:
        if self.steam:
            return self.steam.macos_game
        return None
    
    @Property
    def savegame_root(self)->str|None:
        if not self.game_data:
            return None
        t = Template(self.game_data.savegame_root)
        return t.safe_substitute(self.get_variables())
    
    @Property
    def savegame_dir(self)->str|None:
        if not self.game_data:
            return None
        t = Template(self.game_data.savegame_dir)
        return t.safe_substitute(self.get_variables())
    
    @Property
    def epic(self)->EpicGameData|None:
        return self.__epic
    
    @epic.setter
    def epic(self,epic:EpicGameData|None):
        self.__epic = epic
        
    def add_variable(self,name:str,value:str):
        self.__variables[str(name)] = str(value)
        
    def delete_variable(self,name):
        if name in self.__variables:
            del self.__variables[name]
        
    def get_variables(self):
        vars = settings.get_variables()
        vars.update(self.__variables)
        game_data = self.game_data
        if game_data is not None:
            vars.update(game_data.get_variables())
        return vars
    
    def get_variable(self,name):
        try:
            return self.get_variables()[name]
        except:
            return ""        
            
    def serialize(self)->dict:
        ret = {
            'key': self.key,
            'name': self.name,
            'savegame_name': self.savegame_name,
            'savegame_type': self.savegame_type.value,
            'is_active': self.is_active,
            'is_live': self.is_live,
        }
        if self.dbid:
            ret['dbid'] = self.dbid
        
        if (self.windows and self.windows.is_valid):
            ret['windows'] = self.windows.serialize()
        if (self.linux and self.linux.is_valid):
            ret['linux'] = self.linux.serialize()
        if (self.macos and self.macos.is_valid):
            ret['macos'] = self.macos.serialize()
        if (self.steam):
            ret['steam'] = self.steam.serialize()
        if (self.epic and self.epic.is_valid):
            ret['epic'] = self.epic.serialize()
        #if self.gog_windows:
        #    ret['gog_windows'] = self.gog_windows.serialize()
        #if self.gog_linux:
        #    ret['gog_linux'] = self.gog_linux.serialize()
        
        return ret
    
    def save(self):
        path = pathlib.Path(self.filename).resolve() if self.filename else None
        if path is None:
            logger.error("No filename for saving the game \"{game}\" set! Not saving file!".format(game=self.name))
            return
        
        if hasattr(self,'__old_filename'):
            old_path = pathlib.Path(self.__old_filename).resolve()
            if  old_path.is_file():
                os.unlink(old_path)
            delattr(self,'__old_filename')
            
        if not path.parent.is_dir():
            os.makedirs(path.parent)
            
        with open(path,'wt',encoding='utf-8') as ofile:
            ofile.write(json.dumps(self.serialize(),ensure_ascii=False,indent=4))
            
        gm = GameManager.get_global()
        if hasattr(self,'_old_key'):
            if self._old_key in gm.games:
                del gm.games[self._old_key]
            delattr(self,'_old_key')
        gm.add_game(self)

    def __bool__(self):
        return (bool(self.game_data) and bool(self.savegame_root) and bool(self.savegame_dir))
    

    def get_backup_files(self)->dict[str:str]|None:
        def get_backup_files_recursive(sgroot:pathlib.Path,sgdir:str,subdir:str|None=None):
            if subdir:
                path = sgroot / sgdir / subdir
            else:
                path = sgroot / sgdir
                
            ret = {}
            for dirent in os.listdir(path):
                file_path = path / dirent
                if file_path.is_file():
                    
                    if subdir:
                        fname = os.path.join(subdir,dirent).replace("\\","/")
                    else:
                        fname = dirent
                        
                    if self.game_data.match(fname):
                        ret[str(file_path)] = os.path.join(sgdir,fname)
                elif file_path.is_dir():
                    if subdir:
                        ret.update(get_backup_files_recursive(sgroot,sgdir,os.path.join(subdir,dirent)))
                    else:
                        ret.update(get_backup_files_recursive(sgroot,sgdir,dirent))
                                
            return ret
        
        if not bool(self):
            return None
        
        sgroot = pathlib.Path(self.savegame_root).resolve()
        sgdir = self.savegame_dir
        sgpath = sgroot / sgdir
        if not os.path.exists(sgpath):
            return None
        
        return get_backup_files_recursive(sgroot,sgdir)
        
    @Property(type=str)
    def savegame_subdir(self)->str:
        """
        savegame_subdir The subdir for the savegame backup.
        
        If `is_live` results to `True`, *"live"* is returned. Else *"finished"* is returned.

        :type: str
        """
        if (self.is_live):
            return "live"
        return "finished"
        
    
class GameManager(GObject):
    __global_gamemanager = None
    logger = logger.getChild('GameManager')
    
    @staticmethod
    def get_global():
        if GameManager.__global_gamemanager is None:
            GameManager.__global_gamemanager = GameManager()
        return GameManager.__global_gamemanager
    
    def __init__(self):
        GObject.__init__(self)
        
        self.__games = {}
        self.__steam_games = {}
        self.__epic_games = {}
        
        self.load()

    @Property(type=object)
    def games(self)->dict[str:Game]:
        return self.__games
    
    @Property
    def steam_games(self)->dict[int:Game]:
        return dict(self.__steam_games)

    def has_steam_game(self,appid:int)->bool:
        return (appid in self.__steam_games)
    @Property
    def epic_games(self)->dict[str:Game]:
        return dict(self.__epic_games)
    
    def has_epic_game(self,catalog_item_id:str)->bool:
        return (catalog_item_id in self.__epic_games)
    
    def load(self):
        if self.__games:
            self.__games = {}
            
        gameconf_dir = settings.gameconf_dir
        if not os.path.isdir(gameconf_dir):
            return
    
        for gcf in (os.path.join(gameconf_dir,i) for i in os.listdir(gameconf_dir)):
            if not os.path.isfile(gcf) or not gcf.endswith('.gameconf'):
                continue
            
            try:
                game = Game.new_from_json_file(gcf)
                if not game:
                    self.logger.warn("Not loaded game \"{game}\"!".format(
                        game=(game.name if game is not None else "UNKNOWN GAME")))
                    continue
            except GLib.Error as ex: #Exception as ex:
                self.logger.error("Unable to load gameconf {gameconf}! ({what})".format(
                    gameconf = os.path.basename(gcf),
                    what = str(ex)))
                continue
            
            self.add_game(game)
        
    def add_game(self,game:Game):
        self.__games[game.key] = game
        if game.steam:
            self.__steam_games[game.steam.appid] = game
        if game.epic:
            self.__epic_games[game.epic.catalog_item_id] = game
            
    def remove_game(self,game:Game|str):
        if isinstance(game,str):
            if key not in self.__games:
                return
            key = game
            game = self.__games[key]
        elif isinstance(game,Game):
            if game.key not in self.__games:
                return
            key = game.key
            
            
        for appid,steam_game in list(self.__steam_games.items()):
            if steam_game.key == game.key:
                del self.__steam_games[appid]
                
        for appname,epic_game in list(self.__epic_games.items()):
            if epic_game.key == game.key:
                del self.__epic_games[appname]
                
        del self.__games[key]
        
