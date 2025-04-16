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

from ..game import Game,SavegameType,VALID_SAVEGAME_TYPES,SAVEGAME_TYPE_ICONS
from ..settings import settings
from ..utility import sanitize_path,sanitize_windows_path
from ..error import NotAnArchiveError

import logging
logger = logging.getLogger(__name__)

class Archiver(GObject):
    def __init__(self,key:str,name:str,extensions:list[str],description:str|None=None):
        GObject.__init__(self)
        self.__key = key
        self.__name = name
        self._logger = logger.getChild("Archiver")
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
            self._logger.warning("[backup] No files SaveGame files for game {game}!".format(game=game.key))
            return False
        
        filename = self.generate_new_backup_filename(game)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
            
        self._logger.info("[backup] {game} -> {filename}".format(
            game=game.key,filename=filename))
        return self.emit('backup',game,filename)
    
    def restore(self,filename:str):
        self.emit('restore',filename)
        
    def generate_new_backup_filename(self,game:Game)->str:
        dt = datetime.datetime.now()
        
        basename = '.'.join((game.savegame_name,
                            dt.strftime("%Y%m%d-%H%M%S"),
                            game.savegame_type.value,
                            game.savegame_subdir,
                            "sgbackup",
                            self.extensions[0][1:] if self.extensions[0].startswith('.') else self.extensions[0]))
        return sanitize_path(os.path.join(settings.backup_dir,
                                          game.savegame_name,
                                          game.savegame_type.value,
                                          game.subdir,
                                          basename))
        
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
    def get_global()->"ArchiverManager":
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
    
    @Signal(name="backup-game-progress",return_type=None,arg_types=(Game,float,str),flags=SignalFlags.RUN_FIRST)
    def do_backup_game_progress(self,game,fraction,message):
        pass
    
    @Signal(name="backup-game-finished",return_type=None,arg_types=(Game,),flags=SignalFlags.RUN_FIRST)
    def do_backup_game_finished(self,game:Game):
        if game.is_live and settings.backup_versions > 0:
            directory = os.path.join(settings.backup_dir,
                                     game.savegame_name,
                                     game.savegame_type.value,
                                     game.savegame_subdir)
            if os.path.isdir(directory):
                files=list(sorted(os.listdir(directory),reverse=True))
                if len(files) > settings.backup_versions:
                    for backup_file in files[settings.backup_versions:]:
                        self.remove_backup(game,backup_file)
    
    @Signal(name="backup-progress",return_type=None,arg_types=(float,),flags=SignalFlags.RUN_FIRST)
    def do_backup_progress(self,fraction):
        pass
    
    @Signal(name="backup-finished",return_type=None,arg_types=(),flags=SignalFlags.RUN_FIRST)
    def do_backup_finished(self):
        pass
    
    @Signal(name="remove-backup",return_type=None,arg_types=(Game,str),flags=SignalFlags.RUN_FIRST)
    def do_remove_backup(self,game,filename):
        logger.info("Removing backup \"{filename}\" for {game}".format(
            filename=os.path.basename(filename),
            game=game.key))
        
        if os.path.isfile(filename):
            os.unlink(filename)
            
    def remove_backup(self,game,filename):
        self.emit("remove-backup",game,filename)
        
    def backup(self,game:Game,multi_backups:bool=False):
        def on_progress(archiver,game,fraction,message):
            self.emit("backup-game-progress",game,fraction,message)
            if not multi_backups:
                self.emit("backup-progress",fraction)
            
        if not multi_backups and self.backup_in_progress:
            raise RuntimeError("A backup is already in progress!!!")
        
        self.backup_in_progress = True
            
        archiver = self.standard_archiver
        backup_sc = archiver.connect('backup-progress',on_progress)
        archiver.backup(game)
        archiver.disconnect(backup_sc)
        if game.is_live and settings.backup_versions > 0:
            backups = sorted(self.get_live_backups_for_type(game,game.savegame_type),reverse=True)
            if backups and len(backups) > settings.backup_versions:
                for filename in backups[settings.backup_versions:]:
                    self.remove_backup(game,filename)
                    
        self.emit("backup-game-finished",game)
        if not multi_backups:
            self.emit("backup-finished")
        self.backup_in_progress = False
        
    def backup_many(self,games:list[Game]):
        def on_game_progress(archiver,game,fraction,message,game_progress,mutex):
            with mutex:
                game_progress[game.key] = fraction
                sum_fractions = 0.0
                for f in game_progress.values():
                    sum_fractions += f
                n = len(game_progress)
            
            progress = ((sum_fractions / n) if n > 0 else 1.0)
            if progress < 0.0:
                progress = 0.0
            elif progress > 1.0:
                progress = 1.0
                
            self.emit('backup-progress',progress)
            
        def thread_function(game):
            self.backup(game,True)

        
        if self.backup_in_progress:
            raise RuntimeError("A backup is already in progress!!!")
        self.backup_in_progress = True
        game_list = list(games)
        
        game_progress = dict([(game.key,0.0) for game in game_list])
        mutex = threading.RLock()
        
        self.__backup_many_game_progress_connection = self.connect('backup-game-progress',on_game_progress,game_progress,mutex)
        threadpool = {}
        
        if settings.backup_threads == 0:
            backup_threads = 1
        else:
            backup_threads = settings.backup_threads
        if len(game_list) > backup_threads:
            n = backup_threads
        else:
            n = len(games)
            
        for i in range(n):
            game=game_list[0]
            del game_list[0]
            
            
            thread = threading.Thread(target=thread_function,args=(game,),daemon=True)
            threadpool[i]=thread
            thread.start()
        
        while threadpool:
            rm_thread=[]
            for i in threadpool.keys():
                thread = threadpool[i]
                if thread.is_alive():
                    continue
                
                if game_list:
                    game = game_list[0]
                    del game_list[0]
                    thread = threading.Thread(target=thread_function,args=(game,),daemon=True)
                    threadpool[i] = thread
                    thread.start()
                else:
                    rm_thread.append(i)
                    
            for i in rm_thread:
                del threadpool[i]
                    
            time.sleep(0.02)
                    
        self.disconnect(self.__backup_many_game_progress_connection)
        self.emit("backup-finished")
        self.backup_in_progress = False
        
    def _on_archiver_backup(self,archiver:Archiver,game:Game,filename:str)->bool:
        return self.emit('backup',archiver,game,filename)
    
    @Signal(name="backup",return_type=bool,arg_types=(Archiver,Game,str),
            flags=SignalFlags.RUN_FIRST)
    def do_backup(self,archiver,game,filename):
        return True
    
    def restore(self,filename:str):
        archiver = self.get_archiver_for_file(filename)
        return self.emit('restore',archiver,filename)
    
    @Signal(name="restore",return_type=bool,arg_types=(Archiver,str),
            flags=SignalFlags.RUN_LAST)
    def do_restore(self,archiver:Archiver,filename:str):
        archiver.restore(filename)
        return True
       
    def is_archive(self,filename:str)->bool:
        if self.standard_archiver.is_archive(filename):
            return True
        for i in self.archivers.values():
            if i.is_archive(filename):
                return True
        return False
    
    def get_archiver_for_file(self,filename:str)->Archiver:
        if self.standard_archiver.is_archive(filename):
            return self.standard_archiver
        
        for archiver in self.archivers.values():
            if archiver.is_archive(filename):
                return archiver
            
        raise NotAnArchiveError(f"\"{filename}\" seems not to be a valid archive!")
            
        
    def get_live_backups(self,game:Game):
        ret = []
        for sgtype in VALID_SAVEGAME_TYPES:
            backupdir = os.path.join(settings.backup_dir,game.savegame_name,sgtype.value,'live')
        
            if os.path.isdir(backupdir):
                for basename in os.listdir(backupdir):
                    filename = os.path.join(backupdir,basename)
                    if (self.is_archive(filename)):
                        ret.append(filename)
                        
        return ret
    
    def get_live_backups_for_type(self,game:Game,type:SavegameType):
        ret = []
        backupdir = os.path.join(settings.backup_dir,game.savegame_name,type.value,'live')
        if (os.path.isdir(backupdir)):
            for basename in os.listdir(backupdir):
                filename = os.path.join(backupdir,basename)
                if (self.is_archive(filename)):
                    ret.append(filename)
        return ret  
    
    def get_finished_backups(self,game:Game):
        ret=[]
        for sgtype in VALID_SAVEGAME_TYPES:
            backupdir = os.path.join(settings.backup_dir,game.savegame_name,sgtype.value,'finished')
        
            if os.path.isdir(backupdir):
                for basename in os.listdir(backupdir):
                    filename = os.path.join(backupdir,basename)
                    if (self.is_archive(filename)):
                        ret.append(filename)
                        
        return ret
    
    def get_backups(self,game:Game):
        ret = []
        for sgtype in VALID_SAVEGAME_TYPES:
            for backupdir in [os.path.join(settings.backup_dir,game.savegame_name,sgtype.value,i) for i in ('live','finished')]:
                if os.path.isdir(backupdir):
                    for basename in os.listdir(backupdir):
                        filename = os.path.join(backupdir,basename)
                        if (self.is_archive(filename)):
                            ret.append(filename)
        return ret
