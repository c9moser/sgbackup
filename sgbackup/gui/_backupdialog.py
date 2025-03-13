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

from gi.repository import Gtk,GLib,GObject,Gio
from ..game import GameManager,Game
from ..archiver import ArchiverManager
from ..settings import settings
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
        self.set_modal(True)
        
        self.__ok_button = self.add_button('Close',Gtk.ResponseType.OK)
        
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
            del self.__am_signal_finished
            
        if self.__am_signal_progress is not None:
            am.disconnect(self.__am_signal_progress)
            del self.__am_signal_progress
            
        if settings.gui_autoclose_backup_dialog:
            self.response(Gtk.ResponseType.OK)
        
        return False
            
    def _on_am_backup_game_progress(self,am,game,fraction,message):
        def sanitize_fraction(fraction):
            if fraction < 0.0:
                return 0.0
            if fraction > 1.0:
                return 1.0
            return fraction
        if self.__game.key == game.key:
            GLib.idle_add(self._on_propgress,sanitize_fraction(fraction),message)
            
    def _on_am_backup_game_finished(self,am,game):
        if self.__game.key == game.key:
            GLib.idle_add(self._on_finished)
            
    def run(self):
        def _thread_func(archiver_manager,game):
            am.backup(game)
        self.__ok_button.set_sensitive(False)    
        self.present()
        
        
        am = ArchiverManager.get_global()
        if not hasattr(self,'__am_signal_progress'):
            self.__am_signal_progress = am.connect('backup-game-progress',self._on_am_backup_game_progress)
        if not hasattr(self,'__am_signal_finished'):
            self.__am_signal_finished = am.connect('backup-game-finished',self._on_am_backup_game_finished)
        thread = Thread(target=_thread_func,args=(am,self.__game),daemon=True)
        thread.start()

class BackupGameData(GObject.GObject):
    def __init__(self,game:Game):
        GObject.GObject.__init__(self)
        self.__progress = 0.0
        self.__game = game
        self.__finished = False

    @GObject.Property
    def game(self)->Game:
        return self.__game

    @GObject.Property(type=str)
    def key(self)->str:
        return self.__game.key
        
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
        
    @GObject.Property(type=bool,nick='finished',default=False)
    def finished(self)->bool:
        return self.__finished
    
    @finished.setter
    def finished(self,is_finished:bool):
        self.__finished = is_finished
        
class BackupGameDataSorter(Gtk.Sorter):
    def do_compare(self,item1,item2):
        name1 = item1.game.name.lower()
        name2 = item2.game.name.lower()
        
        if item1.finished:
            if not item2.finished:
                return Gtk.Ordering.SMALLER
            elif name1 > name2:
                return Gtk.Ordering.LARGER
            elif name1 < name2:
                return Gtk.Ordering.SMALLER
            else:
                return Gtk.Ordering.EQUAL
        elif item2.finished:
            return Gtk.Ordering.LARGER
        elif item1.progress > item2.progress:
            return Gtk.Ordering.SMALLER
        elif item1.progress < item2.progress:
            return Gtk.Ordering.LARGER
        elif name1 > name2:
            return Gtk.Ordering.LARGER
        elif name1 < name2:
            return Gtk.Ordering.SMALLER
        else:
            return Gtk.Ordering.EQUAL


class BackupManyDialog(Gtk.Dialog):
    logger = logger.getChild('BackupMultiDialog')
    def __init__(self,parent:Gtk.Window|None=None,games:list[Game]|None=None):
        Gtk.Dialog.__init__(self)
        if parent:
            self.set_transient_for(parent)
        self.set_decorated(False)
        self.set_modal(True)
        self.set_default_size(640,480)        
                
        self.__scrolled = Gtk.ScrolledWindow()
        self.__games_liststore = Gio.ListStore.new(BackupGameData)
        self.__games_progress_sorter = BackupGameDataSorter()
        self.__games_sortmodel = Gtk.SortListModel.new(self.__games_liststore,
                                                       self.__games_progress_sorter)
        self.__games_selection = Gtk.SingleSelection.new(self.__games_sortmodel)
        
        name_factory = Gtk.SignalListItemFactory()
        name_factory.connect('setup',self._on_column_name_setup)
        name_factory.connect('bind',self._on_column_name_bind)
        name_column = Gtk.ColumnViewColumn.new('Name',name_factory)
        
        progress_factory = Gtk.SignalListItemFactory()
        progress_factory.connect('setup',self._on_column_progress_setup)
        progress_factory.connect('bind',self._on_column_progress_bind)
        progress_column = Gtk.ColumnViewColumn.new('Progress',progress_factory)
        progress_column.set_expand(True)
        
        self.__games_columnview = Gtk.ColumnView.new(self.__games_selection)
        self.__games_columnview.set_vexpand(True)
        self.__games_columnview.append_column(name_column)
        self.__games_columnview.append_column(progress_column)
        
        self.__scrolled.set_child(self.__games_columnview)
        self.__scrolled.set_vexpand(True)
        self.get_content_area().append(self.__scrolled)
        
        self.__progressbar = Gtk.ProgressBar()
        self.__progressbar.set_hexpand(True)
        self.__progressbar.set_show_text(False)
        self.get_content_area().append(self.__progressbar)

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
                    self.__games = {}
                    raise TypeError("\"games\" is not an Iterable of \"Game\" instances!")
                if g.get_backup_files():
                    self.__games.append(g)
        if self.__games:
            self.__ok_button.set_sensitive(False)
        else:
            self.__ok_button.set_sensitive(True)
    
    def do_response(self,response):
        self.hide()
        self.destroy()
        
    def run(self):
        def thread_func(am,games):
            am.backup_many(games)
            return 0
        
        def on_am_backup_game_progress(am,game,progress,message):
            GLib.idle_add(self._on_backup_game_progress,game,progress)
            
        def on_am_backup_game_finished(am,game):
            GLib.idle_add(self._on_backup_game_finished,game)
            
        def on_am_backup_progress(am,progress):
            GLib.idle_add(self._on_backup_progress,progress)
            
        def on_am_backup_finished(am):
            GLib.idle_add(self._on_backup_finished)
            
        if not self.games:
            logger.warning("No games to backup!")
            self.hide()
            self.destroy()
            self.response(Gtk.Response.OK)
            return
        
        self.__ok_button.set_sensitive(False)
        
        am = ArchiverManager.get_global()
        
        if not hasattr(self,'__signal_backup_progress'):
            self.__signal_backup_progress =  am.connect('backup-progress',
                                                        on_am_backup_progress)
        if not hasattr(self,'__signal_backup_finished'):
            self.__signal_backup_finished = am.connect('backup-finished',
                                                       on_am_backup_finished)    
        if not hasattr(self,'__signal_backup_game_progress'):
            self.__signal_backup_game_progress = am.connect('backup-game-progress',
                                                            on_am_backup_game_progress)    
        if not hasattr(self,'__signal_backup_game_finished'):
            self.__signal_backup_game_finished = am.connect('backup-game-finished',
                                                            on_am_backup_game_finished)
                
        thread = Thread(target=thread_func,args=(am,list(self.__games)),daemon=True)
        self.present()
        thread.start()        

    
        
    def _on_column_name_setup(self,factory,item):
        label = Gtk.Label()
        label.set_xalign(0.0)
        item.set_child(label)
        
    def _on_column_name_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_text(data.game.name)
        
    def _on_column_progress_setup(self,factory,item):
        progressbar = Gtk.ProgressBar()
        progressbar.set_show_text(False)
        progressbar.set_hexpand(True)
        item.set_child(progressbar)
        
    def _on_column_progress_bind(self,factory,item):
        progressbar = item.get_child()
        data = item.get_item()
        
        if not hasattr(progressbar,'_property_progress_binding'):
            progressbar._property_progress_binding = data.bind_property('progress',progressbar,'fraction',GObject.BindingFlags.SYNC_CREATE)
            
    def _on_backup_game_progress(self,game:Game,progress:float):
        for i in reversed(range(self.__games_liststore.get_n_items())):
            gamedata = self.__games_liststore.get_item(i)
            if gamedata.key == game.key:
                gamedata.progress = progress
                self.__games_progress_sorter.changed(Gtk.SorterChange.DIFFERENT)
                return
        gamedata = BackupGameData(game)
        gamedata.progress = progress
        self.__games_liststore.append(gamedata)
        vadjustment = self.__scrolled.get_vadjustment()
        vadjustment.set_value(vadjustment.get_upper() - vadjustment.get_page_size())
        
        return False
        
    def _on_backup_game_finished(self,game):
        for i in reversed(range(self.__games_liststore.get_n_items())):
            gamedata = self.__games_liststore.get_item(i)
            if gamedata.key == game.key:
                gamedata.progress = 1.0
                gamedata.finished = True
                self.__games_progress_sorter.changed(Gtk.SorterChange.DIFFERENT)
                return
        gamedata = BackupGameData(game)
        gamedata.progress = 1.0
        gamedata.finished = True
        self.__games_liststore.append(gamedata)
        self.__games_progress_sorter.changed(Gtk.SorterChange.DIFFERENT)
        vadjustment = self.__scrolled.get_vadjustment()
        vadjustment.set_value(vadjustment.get_upper() - vadjustment.get_page_size())

        return False
        
    def _on_backup_progress(self,progress:float):
        self.__progressbar.set_fraction(progress)
        
        return False
        
    def _on_backup_finished(self):
        self.__progressbar.set_fraction(1.0)
        self.__ok_button.set_sensitive(True)
        self.set_decorated(True)
        
        am = ArchiverManager.get_global()
        if hasattr(self,'__signal_backup_game_finished'):
            am.diconnect(self.__signal_backup_game_finished)
            del self.__signal_backup_game_finished
        if hasattr(self,'__signal_backup_game_progress'):
            am.disconnect(self.__signal_backup_game_progress)
            del self.__signal_backup_game_progress
        if hasattr(self,'__signal_backup_finished'):
            am.disconnect(self.__signal_backup_finished)
            del self.__signal_backup_finished
        if hasattr(self,'__signal_backup_progress'):
            am.disconnect(self.__signal_backup_progress)
            del self.__signal_backup_progress

        if settings.gui_autoclose_backup_dialog:
            self.response(Gtk.ResponseType.OK)
                    
        return False
        
        
