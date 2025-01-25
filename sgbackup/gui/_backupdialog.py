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

from gi.repository import Gtk,GLib
from ..game import GameManager,Game
from ..archiver import ArchiverManager
from threading import Thread,ThreadError

class BackupSingleDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window,game:Game):
        Gtk.Dialog.__init__(self)
        self.set_title("sgbackup: Backup -> {game}".format(game=game.name))
        self.set_decorated(False)
        self.__game = game
        
        self.set_transient_for(parent)
        
        self.__progressbar = Gtk.ProgressBar()
        self.__progressbar.set_text("Starting savegame backup ...")
        self.__progressbar.set_fraction(0.0)
        
        self.get_content_area().append(self.__progressbar)
        self.set_modal(False)
        
        self.__am_signal_progress = None
        self.__am_signal_finished = None
        
        
    def _on_propgress(self,fraction,message):
        self.__progressbar.set_text(message if message else "Working ...")
        self.__progressbar.set_fraction(fraction)
        return False
        
    def _on_finished(self):
        self.__progressbar.set_text("Finished ...")
        self.__progressbar.set_fraction(1.0)
        am = ArchiverManager.get_global()
        if self.__am_signal_finished is not None:
            am.disconnect(self.__am_signal_finished)
            self.__am_signal_finished = None
            
        if self.__am_signal_progress is not None:
            am.disconnect(self.__am_signal_progress)
            self.__am_signal_progress = None
            
        self.hide()
        self.destroy()
            
    def _on_am_backup_game_progress(self,am,game,fraction,message):
        if self.__game.key == game.key:
            GLib.idle_add(self._on_propgress,fraction,message)
            
    def _on_am_backup_game_finished(self,am,game):
        if self.__game.key == game.key:
            GLib.idle_add(self._on_finished)
            
    def run(self):
        def _thread_func(archiver_manager,game):
            am.backup(game)
            
        self.present()
        
        am = ArchiverManager.get_global()
        self.__am_signal_progress = am.connect('backup-game-progress',self._on_am_backup_game_progress)
        self.__am_signal_finished = am.connect('backup-game-finished',self._on_am_backup_game_finished)
        thread = Thread(target=_thread_func,args=(am,self.__game),daemon=True)
        thread.start()
        
