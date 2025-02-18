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

from gi.repository import Gtk,GLib,GObject,Gio
from ..game import GameManager,Game
from ..archiver import ArchiverManager
from threading import Thread,ThreadError

import logging

logger = logging.getLogger(__name__)

class BackupSingleDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window,game:Game):
        Gtk.Dialog.__init__(self)
        self.set_title("sgbackup: Backup -> {game}".format(game=game.name))
        self.set_decorated(False)
        self.__game = game
        
        self.set_transient_for(parent)
        
        label = Gtk.Label()
        label.set_markup("<span size=\"x-large\">Backing up <i>{game}</i></span>".format(
            game = GLib.markup_escape_text(game.name)))
        
        self.get_content_area().append(label)
        
        self.__progressbar = Gtk.ProgressBar()
        self.__progressbar.set_text("Starting savegame backup ...")
        self.__progressbar.set_show_text(True)
        self.__progressbar.set_fraction(0.0)
        
        self.get_content_area().append(self.__progressbar)
        self.set_modal(False)
        
        self.__ok_button = self.add_button('Close',Gtk.ResponseType.OK)
        self.__am_signal_progress = None
        self.__am_signal_finished = None
        
        
    def _on_propgress(self,fraction,message):
        self.__progressbar.set_text(message if message else "Working ...")
        self.__progressbar.set_fraction(fraction)
        return False
        
    def do_response(self,response):
        self.hide()
        self.destroy()
        
    def _on_finished(self):
        self.__progressbar.set_text("Finished ...")
        self.__progressbar.set_fraction(1.0)
        self.__ok_button.set_sensitive(True)
        am = ArchiverManager.get_global()
        
        if self.__am_signal_finished is not None:
            am.disconnect(self.__am_signal_finished)
            self.__am_signal_finished = None
            
        if self.__am_signal_progress is not None:
            am.disconnect(self.__am_signal_progress)
            self.__am_signal_progress = None
            
        #if settings.backup_dialog_close_when_finished:
        #    self.response(Gtk.ResponseType.OK)
        
        return False
            
    def _on_am_backup_game_progress(self,am,game,fraction,message):
        if self.__game.key == game.key:
            GLib.idle_add(self._on_propgress,fraction,message)
            
    def _on_am_backup_game_finished(self,am,game):
        if self.__game.key == game.key:
            GLib.idle_add(self._on_finished)
            
    def run(self):
        def _thread_func(archiver_manager,game):
            am.backup(game)
        self.__ok_button.set_sensitive(False)    
        self.present()
        
        
        am = ArchiverManager.get_global()
        self.__am_signal_progress = am.connect('backup-game-progress',self._on_am_backup_game_progress)
        self.__am_signal_finished = am.connect('backup-game-finished',self._on_am_backup_game_finished)
        thread = Thread(target=_thread_func,args=(am,self.__game),daemon=True)
        thread.start()

class BackupGameData(GObject.GObject):
    def __init__(self,game:Game):
        GObject.__init__(self)
        self.__progress = 0.0
        self.__game = game

    @GObject.Property
    def game(self)->Game:
        return self.__game

    @GObject.Property(type=float)
    def progress(self)->float:
        return self.__progress
    
    @progress.setter
    def progress(self,fraction:float):
        if fraction < 0.0:
            fraction = 0.0
        elif fraction > 1.0:
            fraction = 1.0

        self.__progress = fraction

class BackupMultiDialog(Gtk.Dialog):
    logger = logger.getChild('BackupMultiDialog')
    def __init__(self,parent:Gtk.Window|None=None,games:list[Game]|None=None):
        Gtk.Dialog.__init__(self)
        if parent:
            self.set_transient_for(parent)

        self.__scrolled = Gtk.ScrolledWindow()
        self.__games_liststore = Gio.Liststore(BackupGameData)

        self.__ok_button = self.add_button("Close",Gtk.ResponseType.OK)

        self.games = games

        

    @GObject.Property
    def games(self)->list[Game]:
            return self.__games
    
    @games.setter
    def games(self,games:list[Game]|None):
        self.__games = []
        if games:
            for g in games:
                if not isinstance(g,Game):
                    self.__games = []
                    raise TypeError("\"games\" is not an Iterable of \"Game\" instances!")
                if g.get_backup_files():
                    self.__games.append(Game)
        if self.__games:
            self.__ok_button.set_sensitive(False)
        else:
            self.__ok_button.set_sensitive(True)