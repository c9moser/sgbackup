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

from configparser import ConfigParser
import os
import sys

from gi.repository import GLib,GObject
import zipfile
from threading import RLock

from .utility import (
    sanitize_path,
    sanitize_windows_path,
    PLATFORM_WINDOWS,
    PLATFORM_MACOS,
    PLATFORM_LINUX,
    PLATFORM_UNIX
)


ZIPFILE_COMPRESSION_STR = {
    zipfile.ZIP_STORED: "stored",
    zipfile.ZIP_DEFLATED: "deflated",
    zipfile.ZIP_BZIP2: "bzip2",
    zipfile.ZIP_LZMA: "lzma",
}

ZIPFILE_COMPRESSLEVEL_MAX = {
    zipfile.ZIP_STORED: 0,
    zipfile.ZIP_DEFLATED: 9,
    zipfile.ZIP_BZIP2: 9,
    zipfile.ZIP_LZMA: 0,
}

ZIPFILE_STR_COMPRESSION = {}
for _zc,_zs in ZIPFILE_COMPRESSION_STR.items():
    ZIPFILE_STR_COMPRESSION[_zs] = _zc
del _zc
del _zs

    
class Settings(GObject.GObject):
    __gtype_name__ = "Settings"
    
    def __init__(self):
        super().__init__()
        self.__mutex = RLock()
        
        self.__keyfile = GLib.KeyFile.new()
        self.__config_dir = os.path.join(GLib.get_user_config_dir(),'sgbackup')
        self.__gameconf_dir = os.path.join(self.__config_dir,'games')
        self.__logger_conf = os.path.join(self.__config_dir,'logger.conf')
        self.__backup_versions = 0
        
        self.__config_file = os.path.join(self.__config_dir,'sgbackup.conf')
        if (os.path.isfile(self.__config_file)):
            self.__keyfile.load_from_file(self.__config_file,
                                          (GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS))
                
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir)
            
        if not os.path.isdir(self.gameconf_dir):
            os.makedirs(self.gameconf_dir)

    def _has_group_nb(self,group:str)->bool:
        return self.keyfile.has_group(group)
    
    def has_group(self,group:str)->bool:
        with self.__mutex:
            return self._has_group_nb(group)
    
    def has_section(self,section:str)->bool:
        with self.__mutex:
            return self._has_group_nb(section)
    
    def _has_key_nb(self,group:str,key:str)->bool:
        if self._has_group_nb(group):
            keys,length = self.keyfile.get_keys(group)
            return (key in keys)
        return False
    
    def has_option(self,section:str,option:str):
        with self.__mutex:
            return self._has_key_nb(section,option)
    
    def has_key(self,group:str,key:str):
        with self.__mutex:
            return self._has_key_nb(group,key)
    
    def get_groups(self):
        with self.__mutex:
            return self.keyfile.get_groups()[0]
    
    def get_sections(self):
        with self.__mutex:
            return self.keyfile.get_groups()[0]
    
    def get_keys(self,group:str):
        with self.__mutex:
            if not self._has_group_nb(group):
                return []
            return self.keyfile.get_keys(group)[0]
    
    def get_options(self,section:str):
        with self.__mutex:
            if not self._has_group_nb(section):
                return []
            return self.keyfile.get_keys(section)[0]
    
    def get(self,group:str,key:str,default=None)->str|None:
        with self.__mutex:
            if (self._has_key_nb(group,key)):
                self.keyfile.get_value(group,key)
        return default
    
    def set(self,group:str,key:str,value:str):
        with self.__mutex:
            self.keyfile.set_key(group,key,value)
    
    def get_boolean(self,group:str,key:str,default:bool|None=None)->bool|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_boolean(group,key)
        return default
    
    def set_boolean(self,group:str,key:str,value:bool):
        with self.__mutex:
            self.keyfile.set_boolean(group,key,value)
        
    def get_boolean_list(self,group:str,key:str,default:list[bool]|None=None)->list[bool]|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_boolean_list(group,key)
        return default
    
    def set_boolean_list(self,group:str,key:str,value:list[bool]):
        with self.__mutex:
            self.keyfile.set_boolean_list(group,key,value)
                
    def get_double(self,group:str,key:str,default:float|None=None)->float|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_double(group,key)
        return default
    
    
    def set_double(self,group:str,key:str,value:float):
        with self.__mutex:
            self.keyfile.set_double(group,key,value)
    
    def get_double_list(self,group:str,key:str,default:list[float]|None=None)->list[float]|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_double_list(group,key)
        return default
    
    def set_double_list(self,group:str,key:str,value:list[float]):
        with self.__mutex:
            self.keyfile.set_double_list(group,key,value)
            
    def get_integer(self,group:str,key:str,default:None|int=None)->int|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_integer(group,key)
        return default
    
    def set_integer(self,group:str,key:str,value:int):
        with self.__mutex:
            self.keyfile.set_integer(group,key,value)
        
    def get_integer_list(self,group:str,key:str,default:list[int]|None=None)->list[int]|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_integer_list(group,key)
        return default

    def set_integer_list(self,group:str,key:str,value:list[int]):
        with self.__mutex:
            self.keyfile.set_integer_list(group,key,value)
            
    def get_int64(self,group:str,key:str,default:int|None=None)->int|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                self.keyfile.get_int64(group,key)
        return default
    
    def set_int64(self,group:str,key:str,value:int):
        with self.__mutex:
            self.keyfile.set_int64(group,key,value)
            
    def get_uint64(self,group:str,key:str,default:int|None=None)->int|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                self.keyfile.get_uint64(self,group,key)
        return default
    
    def set_uint64(self,group:str,key:str,value:int):
        with self.__mutex:
            self.keyfile.set_uint64(group,key,value)
        
    def get_locale_for_key(self,group:str,key:str,locale:str|None=None)->str|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_locale_for_key(group,key,locale)
        return None
    
    def get_locale_string(self,group:str,key:str,locale:str|None=None,default:str|None=None)->str|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                ret = self.keyfile.get_locale_string(group,key,locale)
                if ret is not None:
                    return ret
        return default
    
    def set_locale_string(self,group:str,key:str,locale:str,value:str):
        with self.__mutex:
            self.set_locale_string(group,key,locale,value)
            
    def get_locale_string_list(self,group:str,key:str,locale:str|None=None,default:list[str]|None=None)->list[str]|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                ret = self.keyfile.get_locale_string_list(group,key,locale)
                if ret is not None:
                    return ret
        return default
    
    def set_locale_string_list(self,group:str,key:str,locale:str,value:list[str]):
        with self.__mutex:
            self.keyfile.set_locale_string_list(group,key,locale,value)
            
    def get_string(self,group:str,key:str,default:str|None=None)->str|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_string(group,key)
        return default
    
    def set_string(self,group:str,key:str,value:str):
        with self.__mutex:
            self.keyfile.set_string(group,key,value)
            
    def get_string_list(self,group:str,key:str,default:list[str]|None=None)->list[str]|None:
        with self.__mutex:
            if self._has_key_nb(group,key):
                return self.keyfile.get_string_list(group,key)
        return default
    
    def set_string_list(self,group:str,key:str,value:list[str]):
        with self.__mutex:
            self.keyfile.set_string_list(group,key,value)
    
    def remove_key(self,group:str,key:str):
        with self.__mutex:
            if self._has_key_nb(group,key):
                self.keyfile.remove_key(group,key)

    def remove_group(self,group):
        with self.__mutex:
            if self._has_group_nb(group):
                keys = self.keyfile.get_keys(group)[0]
                for key in keys:
                    self.keyfile.remove_key(group,key)
                self.keyfile.remove_group(group)
                
    def remove_comment(self,group:str|None=None,key:str|None=None):
        with self.__mutex:
            try:
                self.keyfile.remove_comment(group,key)
            except:
                pass
            
    def set_comment(self,comment:str,group:str|None=None,key:str|None=None):
        with self.__mutex:
            try:
                self.keyfile.set_comment(group,key,comment)
            except:
                pass
            
    @GObject.Property(nick="parser")
    def parser(self)->GLib.KeyFile:
        return self.__keyfile
    
    @GObject.Property(nick="keyfile")
    def keyfile(self)->GLib.KeyFile:
        return self.__keyfile
    
    @GObject.Property(type=str,nick="config-dir")
    def config_dir(self)->str:
        return self.__config_dir
    
    @GObject.Property(type=str,nick="config-file")
    def config_file(self)->str:
        return self.__config_file
    
    @GObject.Property(type=str,nick="gameconf-dir")
    def gameconf_dir(self)->str:
        return self.__gameconf_dir
    
    @GObject.Property(type=str,nick="logger-conf")
    def logger_conf(self)->str:
        return self.__logger_conf


    @GObject.Property(type=str,nick="backup-dir")
    def backup_dir(self)->str:
        return sanitize_path(self.get_string('sgbackup','backupDirectory',
                                             os.path.join(GLib.get_home_dir(),'SavagameBackups')))
        
    @backup_dir.setter
    def backup_dir(self,directory:str):
        if not os.path.isabs(directory):
            raise ValueError("\"backup_dir\" needs to be an absolute path!")
        return self.set_string('sgbackup','backupDirectory',sanitize_path(directory))
    
    @GObject.Property(type=str)
    def loglevel(self)->str:
        return self.get_string('sgbackup','logLevel',"INFO")

    @GObject.Property(type=int)
    def backup_threads(self)->int:
        return self.get_integer('sgbackup','maxBackupThreads',1)
    
    @backup_threads.setter
    def backup_threads(self,max_threads:int):
        if (max_threads < 1):
            max_threads = 1
        self.set_integer('sgbackup','maxBackupThreads',max_threads)
        
    @GObject.Property(type=int)
    def search_max_results(self)->int:
        return self.get_integer('search','maxResults',10)
    
    @search_max_results.setter
    def search_max_results(self,max:int):
        self.set_integer('search','maxResults',max)
        
    @GObject.Property(type=int)
    def search_min_chars(self)->int:
        return self.get_integer('search','minChars',3)
    
    @search_min_chars.setter
    def search_min_chars(self,min_chars:int):
        self.set_integer('search','minChars',min_chars)
    
    @GObject.Property(type=bool,default=False)
    def gui_autoclose_backup_dialog(self)->bool:
        return self.get_boolean('gui','autocloseBackupDialog',False)
    
    @gui_autoclose_backup_dialog.setter
    def gui_autoclose_backup_dialog(self,autoclose:bool):
        self.set_boolean('gui','autocloseBackupDialog',autoclose)    
    
    @GObject.Property(type=bool,default=False)
    def gui_autoclose_restore_dialog(self)->bool:
        return self.get_boolean('gui','autocloseRestoreDialog',False)
    
    @gui_autoclose_restore_dialog.setter
    def gui_autoclose_restore_dialog(self,autoclose:bool):
        self.set_boolean('gui','autocloseRestoreDialog',autoclose)
    
    @GObject.Property
    def variables(self)->dict[str:str]:
        ret = {}
        if self.keyfile.has_group('variables'):
            for key in self.get_keys('variables'):
                ret[key] = self.get_string('variables',key,"")
        return ret
    @variables.setter
    def variables(self,vars:dict|list|tuple):
        self.remove_group("variables")
        if not vars:
            return
        
        if isinstance(vars,dict):
            for k,v in vars.items():
                self.set_string('variables',k,v)
        else:
            for k,v in dict(vars).items():
                self.set_string('variables',v[0],v[1])
            
    @GObject.Property(type=str)
    def steam_installpath(self):
        if self.has_key('steam','installpath'):
            return self.get_string('steam','installpath')
        
        if PLATFORM_WINDOWS:
            for i in ('SOFTWARE\\WOW6432Node\\Valve\\Steam','SOFTWARE\\Valve\\Steam'):
                try:
                    skey = None
                    skey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,i)
                    svalue = winreg.QueryValueEx(skey,'InstallPath')[0]
                    if svalue:
                        return svalue
                except:
                    continue
                finally:
                    if skey:
                        skey.Close()
        return ""
        
    @steam_installpath.setter
    def steam_installpath(self,path:str):
        self.set_string('steam','installpath',path)

    @GObject.Property
    def epic_datadir(self)->str|None:
        datadir = self.get_string('epic',"dataDir",None)
        if datadir is None and PLATFORM_WINDOWS:
            for i in ("SOFTWARE\\WOW6432Node\\Epic Games\\EpicGamesLauncher","SOFTWARE\\Epic Games\\EpicGamesLauncher"):
                try:
                    skey = None
                    skey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,i)
                    svalue = winreg.QueryValueEx(skey,'AppDataPath')[0]
                    if svalue:
                        datadir = svalue
                        break
                except:
                    continue
                finally:
                    if skey:
                        skey.Close()
        return datadir
    
    @epic_datadir.setter
    def epic_datadir(self,datadir:str|None):
        if not datadir:
            if self.has_key('epic',"dataDir"):
                self.remove_key('epic','dataDir')
            return
        
        if not os.path.isabs(datadir):
            raise ValueError("\"epic_datadir\" is not an absolute path!")
        self.set_string('epic','dataDir',datadir)
        
    @GObject.Property
    def cli_pager(self)->str:
        pager = self.get_string('cli','pager',None)
        if pager is None:
            if PLATFORM_WINDOWS:
                for prg in ['less.exe','more.com']:
                    pager = GLib.find_program_in_path(prg)
                    if pager is not None:
                        return pager
                return ""
            else:
                for prg in ['less','more']:
                    pager = GLib.find_program_in_path(prg)
                    if pager is not None:
                        return pager
            return None
        return pager
    
    @cli_pager.setter
    def cli_pager(self,pager:str):
        value = None
        if not os.path.isabs(pager):
            value = GLib.find_program_in_path(pager)
        elif os.path.isfile(pager):
            value = pager
        if value is not None:
            self.set_string('cli','pager',value)
        else:
            self.remove_key('cli','pager')
    
    def add_variable(self,name:str,value:str):
        self.set_string('variables',name,value)
        
    def remove_variable(self,name:str):
        self.remove_key('variables',name)
        
    def get_variable(self,name:str)->str:
        return self.get_string('variables',name,"")
        
    def get_variables(self)->dict[str:str]:
        if PLATFORM_WINDOWS:
            ret = dict(((name.upper(),value) for name,value in os.environ.items()))
        else:
            ret = dict(os.environ)
        ret.update({
            "DOCUMENTS": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
            "DOCUMENTS_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
            "DATADIR": GLib.get_user_data_dir(),
            "DATA_DIR": GLib.get_user_data_dir(),
            "CONFIGDIR": GLib.get_user_config_dir(),
            "CONFIG_DIR": GLib.get_user_config_dir(),
            "STEAM_INSTALLPATH": self.steam_installpath,
            "DESKTOP_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP),
            "XDG_CONFIG_HOME": GLib.get_user_config_dir(),
            "XDG_DESKTOP_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP),
            "XDG_DOCUMENTS_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
            "DOWNLOADS": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD),
            "XDG_DOWLNLOAD_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD),
            "XDG_PICTURES_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES),
            "XDG_MUSIC_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC),
            "XDG_DATA_HOME": GLib.get_user_data_dir(),
        })
        ret.update(self.variables)
        return ret
        
    @GObject.Property(type=str)
    def archiver(self)->str:
        return self.get_string('sgbackup','archiver',"zipfile")
    
    @archiver.setter
    def archiver(self,archiver_key:str):
        self.set_string('sgbackup','archiver',archiver_key)
        
    @GObject.Property(type=int)
    def backup_versions(self)->int:
        return self.get_integer('sgbackup','backupVersions',0)
    
    @backup_versions.setter
    def backup_versions(self,versions:int):
        self.set_integer('sgbackup','backupVersions',versions)
    
    
    @GObject.Property(type=int)
    def zipfile_compression(self)->int:
        comp = self.get_string('zipfile','compression','deflated')
        try:
            return ZIPFILE_STR_COMPRESSION[comp]
        except:
            pass
        return zipfile.ZIP_DEFLATED
    
    @zipfile_compression.setter
    def zipfile_compression(self,compression:int):
        try:
            self.set_string('zipfile','compression',ZIPFILE_COMPRESSION_STR[compression])
        except:
            self.set_string('zipfile','compression',ZIPFILE_COMPRESSION_STR[zipfile.ZIP_DEFLATED])
            
    @GObject.Property(type=int)
    def zipfile_compresslevel(self)->int:
        cl = self.get_integer('zipfile','compresslevel',9)
        if cl < 0:
            cl = 9
        return cl if cl <= ZIPFILE_COMPRESSLEVEL_MAX[self.zipfile_compression] else ZIPFILE_COMPRESSLEVEL_MAX[self.zipfile_compression]
    
    @zipfile_compresslevel.setter
    def zipfile_compresslevel(self,cl:int):
        self.set_integer('zipfile','compressLevel',cl)
        
    def save(self):
        self.emit('save')

    @GObject.Signal(name='save',flags=GObject.SIGNAL_RUN_LAST,return_type=None,arg_types=())
    def do_save(self):
        with self.__mutex:
            self.keyfile.save_to_file(self.config_file)
    
settings = Settings()
