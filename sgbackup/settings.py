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

class Settings(GObject.GObject):
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
        return GLib.build_filename(GLib.build_filename(GLib.get_home_dir(),'SavagameBackups'))
    @backup_dir.setter
    def backup_dir(self,directory:str):
        if not os.path.isabs(directory):
            raise ValueError("\"backup_dir\" needs to be an absolute path!")
        return self.parser.set('sgbackup','backupDirectory',directory)
    
    @GObject.Property(type=str)
    def loglevel(self)->str:
        if self.parser.has_option('sgbackup','logLevel'):
            return self.parser.get('sgbackup','logLevel')
        return "INFO"

    def save(self):
        self.emit('save')

    @GObject.Signal(name='save',flags=GObject.SIGNAL_RUN_LAST,return_type=None,arg_types=())
    def do_save(self):
        with open(self.config_file,'w') as ofile:
            self.__configparser.write(ofile)
    
settings = Settings()
