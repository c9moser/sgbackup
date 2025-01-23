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

from configparser import ConfigParser
import os
import sys

from gi.repository import GLib,GObject
import zipfile

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
        
        self.__configparser = ConfigParser()
        self.__config_dir = os.path.join(GLib.get_user_config_dir(),'sgbackup')
        self.__gameconf_dir = os.path.join(self.__config_dir,'games')
        self.__logger_conf = os.path.join(self.__config_dir,'logger.conf')
        
        self.__config_file = os.path.join(self.__config_dir,'sgbackup.conf')
        if (os.path.isfile(self.__config_file)):
            with open(self.__config_file,'r') as conf:
                self.__configparser.read_file(conf)
                
        if not os.path.isdir(self.config_dir):
            os.makedirs(self.config_dir)
            
        if not os.path.isdir(self.gameconf_dir):
            os.makedirs(self.gameconf_dir)
            
            
    @GObject.Property(nick="parser")
    def parser(self)->ConfigParser:
        return self.__configparser
    
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
        if self.parser.has_option('sgbackup','backupDirectory'):
           return self.parser.get('sgbackup','backupDirectory')
        return os.path.join(GLib.get_home_dir(),'SavagameBackups')
    @backup_dir.setter
    def backup_dir(self,directory:str):
        if not os.path.isabs(directory):
            raise ValueError("\"backup_dir\" needs to be an absolute path!")
        self.ensure_section('sgbackup')            
        return self.parser.set('sgbackup','backupDirectory',directory)
    
    @GObject.Property(type=str)
    def loglevel(self)->str:
        if self.parser.has_option('sgbackup','logLevel'):
            return self.parser.get('sgbackup','logLevel')
        return "INFO"

    @GObject.Property
    def variables(self)->dict[str:str]:
        ret = {}
        if self.parser.has_section('variables'):
            for k,v in self.parser.items('variables'):
                ret[k] = v
        return ret
    @variables.setter
    def variables(self,vars:dict|list|tuple):
        if self.parser.has_section('variables'):
            for opt in self.parser['variables'].keys():
                self.parser.remove_option('variables',opt)
                
        if not vars:
            return
        
        if isinstance(vars,dict):
            for k,v in vars.items():
                self.parser.set('variables',k,v)
        else:
            for v in vars:
                self.parser.set('variables',v[0],v[1])
            
    def add_variable(self,name:str,value:str):
        self.parser.set('variables',name,value)
        
    def remove_variable(self,name:str):
        try:
            self.parser.remove_option('variables',name)
        except:
            pass
        
    def get_variable(self,name:str)->str:
        try:
            return self.parser.get('variables',name)
        except:
            return ""
        
    def get_variables(self)->dict[str:str]:
        ret = dict(os.environ)
        ret.update({
            "DOCUMENTS": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
            "DOCUMENTS_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
        })
        ret.update(self.variables)
        return ret
        
    @GObject.Property(type=str)
    def zipfile_compression(self)->str:
        if self.parser.has_option('zipfile','compression'):
            try:
                ZIPFILE_STR_COMPRESSION[self.parser.get('zipfile','compression')]
            except:
                pass
        return ZIPFILE_STR_COMPRESSION["deflated"]
    
    @zipfile_compression.setter
    def zipfile_compression(self,compression):
        try:
            self.parser.set('zipfile','compression',ZIPFILE_COMPRESSION_STR[compression])
        except:
            self.parser.set('zipfile','compression',ZIPFILE_STR_COMPRESSION[zipfile.ZIP_DEFLATED])
            
    @GObject.Property(type=int)
    def zipfile_compresslevel(self)->int:
        if self.parser.has_option('zipfile','compressLevel'):
            cl = self.parser.getint('zipfile','compressLevel')
            return cl if cl <= ZIPFILE_COMPRESSLEVEL_MAX[self.zipfile_compression] else ZIPFILE_COMPRESSLEVEL_MAX[self.zipfile_compression]
        return ZIPFILE_COMPRESSLEVEL_MAX[self.zipfile_compression]
    
    @zipfile_compresslevel.setter
    def zipfile_compresslevel(self,cl:int):
        self.parser.set('zipfile','compressLevel',cl)
        
    def save(self):
        self.emit('save')

    def ensure_section(self,section:str):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
                    
    @GObject.Signal(name='save',flags=GObject.SIGNAL_RUN_LAST,return_type=None,arg_types=())
    def do_save(self):
        with open(self.config_file,'w') as ofile:
            self.__configparser.write(ofile)
    
settings = Settings()
