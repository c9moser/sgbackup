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
from .i18n import gettext as _
from .game import GameManager

logger = logging.getLogger(__name__)


class EpicGameInfo(GObject):
    def __init__(self,
                 name:str,
                 installdir:str,
                 catalog_item_id:str,
                 main_catalog_item_id:str):
        GObject.__init__(self)
        
        self.__name = name
        self.__installdir = installdir
        self.__catalog_item_id = catalog_item_id
        self.__main_catalog_item_id = main_catalog_item_id
        
        
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property(type=str)
    def installdir(self)->str:
        return self.__installdir
    
    @Property(type=str)
    def catalog_item_id(self)->str:
        return self.__catalog_item_id
    
    @Property(type=str)
    def main_catalog_item_id(self)->str:
        return self.__main_catalog_item_id
    
    @Property(type=bool,default=False)
    def is_main(self)->bool:
        return (self.catalog_item_id == self.main_catalog_item_id)

class EpicIgnoredApp(GObject):
    def __init__(self,catalog_item_id:str,name:str,reason:str):
        GObject.__init__(self)
        self.__catalog_item_id = catalog_item_id
        self.__name = name
        self.__reason = reason
        
    @Property(type=str)
    def catalog_item_id(self)->str:
        return self.__catalog_item_id
    
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property(type=str)
    def reason(self)->str:
        return self.__reason
    
    def serialize(self):
        return {
            'catalog_item_id':self.catalog_item_id,
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
            with open(self.ignore_file,'r',encoding="utf-8") as ifile:
                data = json.loads(ifile.read())
            
            for i in data:
                ret[i['catalog_item_id']] = EpicIgnoredApp(i['catalog_item_id'],i['name'],i['reason'])
                
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
        
        self.__ignored_apps[app.catalog_item_id] = app
        self.__write_ignore_file()
        
    def remove_ignored_apps(self,app:str|EpicIgnoredApp):
        if isinstance(app,str):
            item_id = app
        elif isinstance(app,EpicIgnoredApp):
            item_id = app.catalog_item_id
        else:
            raise TypeError("app is not a string and not an EpicIgnoredApp instance!")
        
        if item_id in self.__ignored_apps:
            del self.__ignored_apps[item_id]
            self.__write_ignore_file()
            
    @Property
    def ignored_apps(self)->dict[str:EpicIgnoredApp]:
        return dict(self.__ignored_apps)
    
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
            self._logger.error(_("Unable to load Epic manifest \"{manifest}\"! ({error})").format(
                manifest=filename,
                error=str(ex)
            ))
            return None

        if data['FormatVersion'] == 0:
            return EpicGameInfo(
                name=data['DisplayName'],
                installdir=data['InstallLocation'],
                catalog_item_id=data['CatalogItemId'],
                main_catalog_item_id=data['MainGameCatalogItemId']
            )
        return None
    
    def parse_all_manifests(self)->list[EpicGameInfo]:
        manifest_dir=os.path.join(settings.epic_datadir,'Manifests')
        ret = []
        for item in [ i for i in os.listdir(manifest_dir) if i.endswith('.item') ]:
            manifest_file = os.path.join(manifest_dir,item)
            info = self.parse_manifest(manifest_file)
            if info is not None:
                ret.append(info)
                
        return ret
    
    def find_apps(self)->list[EpicGameInfo]:
        return [i for i in self.parse_all_manifests() if i.is_main]
    
    def find_new_apps(self)->list[EpicGameInfo]:
        gm = GameManager.get_global()
        return [i for i in self.find_apps() 
                if not gm.has_epic_game(i.catalog_item_id) and not i.catalog_item_id in self.__ignored_apps]
    