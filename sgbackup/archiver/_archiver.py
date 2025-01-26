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

from gi.repository.GObject import (
    GObject,
    Property,
    Signal,
    SignalFlags,
    signal_accumulator_true_handled,
)

import datetime
import os
import threading
import time

from ..game import Game
from ..settings import settings

class Archiver(GObject):
    def __init__(self,key:str,name:str,extensions:list[str],description:str|None=None):
        GObject.__init__(self)
        self.__key = key
        self.__name = name
        if description:
            self.__description = description
        else:
            self.__description = ""
            
        self.__extensions = list(extensions)
            
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property
    def key(self)->str:
        return self.__key
    
    @Property
    def description(self)->str:
        return self.__description
    
    @Property
    def extensions(self)->list[str]:
        return self.__extensions
    
    def is_archive(self,filename):
        for ext in self.extensions:
            if filename.endswith(ext):
                return True
        return False
            
    def backup(self,game:Game)->bool:
        if not game.get_backup_files():
            return
        filename = self.generate_new_backup_filename(game)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
            
        return self.emit('backup',game,filename)
    
    def generate_new_backup_filename(self,game:Game)->str:
        dt = datetime.datetime.now()
        basename = '.'.join((game.savegame_name,
                            game.savegame_subdir,
                            dt.strftime("%Y%m%d-%H%M%S"),
                            "sgbackup",
                            self.extensions[0][1:]))
        return os.path.join(settings.backup_dir,game.savegame_name,game.subdir,basename)
        
    def _backup_progress(self,game:Game,fraction:float,message:str|None):
        if fraction > 1.0:
            fraction = 1.0
        elif fraction < 0.0:
            fraction = 0.0
            
        self.emit("backup-progress",game,fraction,message)
        
        
    @Signal(name="backup",flags=SignalFlags.RUN_FIRST,
            return_type=bool, arg_types=(GObject,str),
            accumulator=signal_accumulator_true_handled)
    def do_backup(self,game:Game,filename:str):
        raise NotImplementedError("{_class}.{function}() is not implemented!",_class=__class__,function="do_backup")
    
    @Signal(name="restore",flags=SignalFlags.RUN_FIRST,
            return_type=bool,arg_types=(str,),
            accumulator=signal_accumulator_true_handled)
    def do_restore(self,filanme:str):
        raise NotImplementedError("{_class}.{function}() is not implemented!",_class=__class__,function="do_restore")
    
    @Signal(name="backup_progress",flags=SignalFlags.RUN_FIRST,
            return_type=bool,arg_types=(Game,float,str))
    def do_backup_progress(self,game:Game,fraction:float,message:str):
        pass
    
    
    
class ArchiverManager(GObject):
    __global_archiver_manager = None
    
    def __init__(self):
        GObject.__init__(self)
        self.__archivers = {}
        self.__backup_in_progress = False

        
    @staticmethod
    def get_global():
        if ArchiverManager.__global_archiver_manager is None:
            ArchiverManager.__global_archiver_manager = ArchiverManager()
            
        return ArchiverManager.__global_archiver_manager
    
    @property
    def standard_archiver(self)->Archiver:
        try:
            return self.__archivers[settings.archiver]
        except:
            return self.__archivers["zipfile"]
    
    @Property(type=bool,nick='backup-in-progress',default=False)
    def backup_in_progress(self)->bool:
        return self.__backup_in_progress
    @backup_in_progress.setter
    def backup_in_progress(self,b:bool):
        self.__backup_in_progress = b
    
    @property
    def archivers(self):
        return self.__archivers
    
    def _on_archiver_backup_progress_single(self,archiver,game,fraction,message):
        pass
    
    def _on_archiver_backup_progress_multi(self,archiver,game,fraction,message):
        pass
    
    
    @Signal(name="backup-game-progress",return_type=None,arg_types=(Game,float,str),flags=SignalFlags.RUN_FIRST)
    def do_backup_game_progress(self,game,fraction,message):
        pass
    
    @Signal(name="backup-game-finished",return_type=None,arg_types=(Game,),flags=SignalFlags.RUN_FIRST)
    def do_backup_game_finished(self,game:Game):
        pass
    
    @Signal(name="backup-progress",return_type=None,arg_types=(float,),flags=SignalFlags.RUN_FIRST)
    def do_backup_progress(self,fraction):
        pass
    
    @Signal(name="backup-finished",return_type=None,arg_types=(),flags=SignalFlags.RUN_FIRST)
    def do_backup_finished(self):
        pass
    
    def backup(self,game:Game):
        def on_progress(archiver,game,fraction,message):
            self.emit("backup-game-progress",game,fraction,message)
            self.emit("backup-progress",fraction)
            
        if self.backup_in_progress:
            raise RuntimeError("A backup is already in progress!!!")
        
        self.backup_in_progress = True
            
        archiver = self.standard_archiver
        backup_sc = archiver.connect('backup-progress',on_progress)
        archiver.backup(game)
        archiver.disconnect(backup_sc)
        self.emit("backup-game-finished",game)
        self.emit("backup-finished")
        self.backup_in_progress = False
        
    def backup_many(self,games:list[Game]):
        def thread_function(game):
            archiver = self.standard_archiver
            self._on_archiver_backup_progress_multi(archiver,game,1.0,"Finished ...")
        
        if self.backup_in_progress:
            raise RuntimeError("A backup is already in progress!!!")
        self.backup_in_progress = True
        game_list = list(games)
        threadpool = {}
        
        if len(game_list) > 8:
            n = 8
        else:
            n = len(games)
            
        for i in range(n):
            game=game_list[0]
            del game_list[0]
            
            thread = threading.Thread(thread_function,args=game,daemon=True)
            threadpool.append(thread)
            thread.start()
        
        while threadpool:
            time.sleep(0.02)
            for i in range(len(threadpool)):
                thread = threadpool[i]
                if thread.is_alive():
                    continue
                del threadpool[i]
                
                if game_list:
                    game = game_list[0]
                    del game_list[0]
                    thread = threading.Thread(thread_function,args=game,daemon=True)
                    threadpool.append(thread)
                    thread.start()
        self.backup_in_progress = False
       
    def is_archive(self,filename)->bool:
        if self.standard_archiver.is_archive(filename):
            return True
        for i in self.archivers.values():
            if i.is_archive(filename):
                return True
        return False
        
    def get_backups(self,game:Game):
        ret = []
        for backupdir in [os.path.join(settings.backup_dir,game.savegame_name,i) for i in ('live','finished')]:
            if os.path.isdir(backupdir):
                for basename in os.listdir(backupdir):
                    filename = os.path.join(backupdir,basename)
                    if (self.is_archive(filename)):
                        ret.append(filename)
                        
        return ret
            
        