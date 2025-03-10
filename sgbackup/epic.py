###############################################################################
# sgbackup - The SaveGame Backup tool                                         #
#    Copyright (C) 2024,2025  Christian Moser                                 #
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

import sys,os
from gi.repository import GLib
from gi.repository.GObject import GObject,Signal,SignalFlags,Property

from .settings import settings
import json

import logging
from i18n import gettext as _

logger = logging.getLogger(__name__)

PLATFORM_WINDOWS = sys.platform.lower().startswith('win')

class EpicGameInfo(GObject):
    def __init__(self,
                 name:str,
                 installdir:str,
                 appname:str,
                 main_appname:str):
        GObject.__init__(self)
        
        self.__name = name
        self.__installdir = installdir
        self.__appname = appname
        self.__main_appname = main_appname
        
        
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property(type=str)
    def installdir(self)->str:
        return self.__installdir
    
    @Property(type=str)
    def appname(self)->str:
        return self.__appname
    
    @Property(type=str)
    def main_appname(self)->str:
        return self.__main_appname
    
    @Property(type=bool,default=False)
    def is_main(self)->bool:
        return (self.appname == self.main_appname)

class EpicIgnoredApp(GObject):
    def __init__(self,appname:str,name:str,reason:str):
        GObject.__init__(self)
        self.__appname = appname
        self.__name = name
        self.__reason = reason
        
    @Property(type=str)
    def appname(self)->str:
        return self.__appname
    
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property(type=str)
    def reason(self)->str:
        return self.__reason
    
    def serialize(self):
        return {
            'appname':self.appname,
            'name':self.name,
            'reason':self.reason,
        }
    

class Epic(GObject):
    _logger = logger.getChild('Epic')
    
    
    def __init__(self):
        GObject.__init__(self)
        self.__ignored_apps=self.__parse_ignore_file()
        
        
    @Property(type=str)
    def ignore_file(self)->str:
        return os.path.join(settings.config_dir,'epic.ignore')
    
    def __parse_ignore_file(self)->dict[str:EpicIgnoredApp]:
        ret = {}
        if os.path.isfile(self.ignore_file):
            with open(self.ignore_file,'r',encoding="urf-8") as ifile:
                data = json.loads(ifile.read())
            
            for i in data:
                ret[i['appname']] = EpicIgnoredApp(i['appname'],i['name'],i['reason'])
                
        return ret
    
    def __write_ignore_file(self):
        with open(self.ignore_file,'w',encoding="utf-8") as ofile:
            ofile.write(json.dumps(
                [v.serialize() for v in self.__ignored_apps.values()],
                ensure_ascii=False,
                indent=4))
        
    def add_ignored_app(self,app:EpicIgnoredApp):
        if not isinstance(app,EpicIgnoredApp):
            raise TypeError('app is not an EpicIgnoredApp instance!')
        
        self.__ignored_apps[app.appname] = app
        self.__write_ignore_file()
        
    def remove_ignored_apps(self,app:str|EpicIgnoredApp):
        if isinstance(app,str):
            appname = app
        elif isinstance(app,EpicIgnoredApp):
            appname = app.appname
        else:
            raise TypeError("app is not a string and not an EpicIgnoredApp instance!")
        
        if appname in self.__ignored_apps:
            del self.__ignored_apps[appname]
            self.__write_ignore_file()
            
    @Property
    def ignored_apps(self)->dict[str:EpicIgnoredApp]:
        return self.__ignored_apps
    
    @Property(type=str)
    def datadir(self):
        return settings.epic_datadir if settings.epic_datadir is not None else ""
    
    def parse_manifest(self,filename)->EpicGameInfo|None:
        if not os.path.exists(filename):
            return None
        if not filename.endswith('.item'):
            return None
        
        try:
            with open(filename,'r',encoding="utf-8") as ifile:
                data = json.loads(ifile.read())
        except Exception as ex:
            self._logger.error(_("Unable ot load Epic manifest \"{manifest}\"! ({error})").format(
                manifest=filename,
                error=str(ex)
            ))
            return None

        if data['FormatVersion'] == 0:
            return EpicGameInfo(
                name=data['DisplayName'],
                installdir=data['InstallLocation'],
                appname=data['AppName'],
                main_appname=data['MainGameAppName']
            )
        return None
    
    def parse_all_manifests(self)->list[EpicGameInfo]:
        manifest_dir=os.path.join(settings.epic_datadir,'Manifests')
        ret = []
        for item in [ i for i in os.listdir(manifest_dir) if i.endswith('.item') ]:
            manifest_file = os.path.join(manifest_dir,item)
            info = self.parse_manifest(manifest_file)
            if info is not None:
                ret += info
                
        return ret
    
    def get_apps(self)->list[EpicGameInfo]:
        return [i for i in self.parse_all_manifests() if i.appname == i.main_appname]
    
    def get_new_apps(self)->list[EpicGameInfo]:
        return []
    