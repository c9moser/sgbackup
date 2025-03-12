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

from gi.repository import Gtk,Gio,Gdk,GLib
from gi.repository.GObject import GObject,Signal,Property,SignalFlags,BindingFlags
from ..i18n import gettext as _, noop as N_,pgettext,npgettext,ngettext,TEXTDOMAIN

import rapidfuzz

import logging; logger=logging.getLogger(__name__)

import os,sys
from datetime import datetime as DateTime
from pathlib import Path

from ..settings import settings
from ._settingsdialog import SettingsDialog
from ._gamedialog import GameDialog
from ..game import (
    Game,
    GameManager,
    SAVEGAME_TYPE_ICONS,
    SavegameType,
    GAME_PROVIDER_ICONS,
    GameProvider
)
from ._steam import (
    SteamLibrariesDialog,
    NewSteamAppsDialog,
    SteamNoNewAppsDialog,
    SteamNoIgnoredAppsDialog,
    SteamIgnoreAppsDialog,
)
from ..steam import Steam
from ..epic import Epic
from ._epic import EpicNewAppsDialog
from ._backupdialog import BackupSingleDialog,BackupManyDialog
from ..archiver import ArchiverManager
from ._dialogs import (
    AboutDialog,
    NoGamesToBackupDialog,
    NoGamesToBackupFoundDialog,
)

__gtype_name__ = __name__

class GameViewData(GObject):
    """
    GameViewData Data class for the GameView.columnview
    """
    def __init__(self,game:Game):
        GObject.__init__(self)
        self.__game = game
        self.__fuzzy_match = 0.0
        
    @property
    def game(self)->Game:
        """
        game The game to display [*read/write*]

        :type: 
        """
        return self.__game
    
    @Property(type=str)
    def name(self)->str:
        """
        name The name of the game.
        
        If you need a property-binding use game.name.

        :type: str
        """
        return self.game.name
    
    @Property(type=str)
    def key(self)->str:
        """
        key The game's key.

        :type: str
        """
        return self.game.key
    
    @Property
    def savegame_type(self)->SavegameType:
        """
        savegame_type The SaveGameType

        :type: SavegameType
        """
        return self.game.savegame_type
    
    @Property(type=float)
    def fuzzy_match(self)->float:
        """
        fuzzy_match The value of QCompare of the game name against a search entry.

        :type: float
        """
        return self.__fuzzy_match
    
    @fuzzy_match.setter
    def fuzzy_match(self,match:float):
        self.__fuzzy_match = match
        
        
class GameViewKeySorter(Gtk.Sorter):
    def __init__(self,sort_ascending:bool=True,*args,**kwargs):
        Gtk.Sorter.__init__(self)
        
        self.sort_ascending = sort_ascending
        
    @Property(type=bool,default=True)
    def sort_ascending(self)->bool:
        return self.__sort_ascending
    @sort_ascending.setter
    def sort_ascending(self,asc:bool):
        self.__sort_ascending = asc
    
    def do_compare(self,game1,game2):
        if self.sort_ascending:
            if game1.key > game2.key:
                return Gtk.Ordering.LARGER
            elif game1.key < game2.key:
                return Gtk.Ordering.SMALLER
            else:
                return Gtk.Ordering.EQUAL
        else:
            if game1.key < game2.key:
                return Gtk.Ordering.LARGER
            elif game1.key > game2.key:
                return Gtk.Ordering.SMALLER
            else:
                return Gtk.Ordering.EQUAL
            
class GameViewNameSorter(Gtk.Sorter):
    def __init__(self,sort_ascending:bool=True,*args,**kwargs):
        Gtk.Sorter.__init__(self)
        
        self.sort_ascending = sort_ascending
        
    @Property(type=bool,default=True)
    def sort_ascending(self)->bool:
        return self.__sort_ascending
    @sort_ascending.setter
    def sort_ascending(self,asc:bool):
        self.__sort_ascending = asc
    
    def do_compare(self,game1,game2):
        name1 = game1.name.lower()
        name2 = game2.name.lower()
        
        if self.sort_ascending:
            if name1 > name2:
                return Gtk.Ordering.LARGER
            elif name1 < name2:
                return Gtk.Ordering.SMALLER
            else:
                return Gtk.Ordering.EQUAL
        else:
            if name1 < name2:
                return Gtk.Ordering.LARGER
            elif name1 > name2:
                return Gtk.Ordering.SMALLER
            else:
                return Gtk.Ordering.EQUAL
            
        
class GameViewMatchSorter(Gtk.Sorter):
    def do_compare(self,item1:GameViewData,item2:GameViewData):
        if item1.fuzzy_match < item2.fuzzy_match:
            return Gtk.Ordering.LARGER
        elif item1.fuzzy_match > item2.fuzzy_match:
            return Gtk.Ordering.SMALLER
        
        name1 = item1.name.lower()
        name2 = item2.name.lower()
        if name1 > name2:
            return Gtk.Ordering.LARGER
        elif name1 < name2:
            return Gtk.Ordering.SMALLER
        else:
            return Gtk.Ordering.EQUAL

class GameViewMatchFilter(Gtk.Filter):
    def do_match(self,item:GameViewData|None):
        if item is None:
            return False
        
        return item.fuzzy_match > 0.0

class GameView(Gtk.Box):
    """
    GameView The View for games.
        
    This is widget presents a clumnview for the installed games.
    """
    __gtype_name__ = "GameView"
    
    def __init__(self):
        """
        GameView
        """
        Gtk.Box.__init__(self,orientation=Gtk.Orientation.VERTICAL)
        self.__key_sorter = GameViewKeySorter(True)
        self.__name_sorter = GameViewNameSorter(True)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        # set up the ActionBar for this widget
        self.__actionbar = Gtk.ActionBar()
        self.actionbar.set_hexpand(True)
        
        icon = Gtk.Image.new_from_icon_name('list-add-symbolic')
        icon.set_pixel_size(16)
        add_game_button = Gtk.Button()
        add_game_button.set_child(icon)
        add_game_button.set_tooltip_text(_("Add a new game."))
        add_game_button.connect('clicked',self._on_add_game_button_clicked)
        self.actionbar.pack_start(add_game_button)
                
        icon = Gtk.Image.new_from_icon_name(GAME_PROVIDER_ICONS[GameProvider.STEAM])
        icon.set_pixel_size(16)
        new_steam_games_button = Gtk.Button()
        new_steam_games_button.set_child(icon)
        new_steam_games_button.set_tooltip_text(_("Manage new Steam-Apps."))
        new_steam_games_button.connect('clicked',self._on_new_steam_games_button_clicked)
        self.actionbar.pack_start(new_steam_games_button)
        
        icon = Gtk.Image.new_from_icon_name(GAME_PROVIDER_ICONS[GameProvider.EPIC_GAMES])
        icon.set_pixel_size(16)
        new_epic_games_button = Gtk.Button()
        new_epic_games_button.set_child(icon)
        new_epic_games_button.set_tooltip_text(_("Manage new Epic-Games apps"))
        new_epic_games_button.connect('clicked',self._on_new_epic_games_button_clicked)
        self.actionbar.pack_start(new_epic_games_button)
        
        self.actionbar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        icon = Gtk.Image.new_from_icon_name('document-save-symbolic')
        icon.set_pixel_size(16)
        backup_active_live_button = Gtk.Button()
        backup_active_live_button.set_child(icon)
        backup_active_live_button.set_tooltip_markup(_("Backup all <i>active</i> and <i>live</i> Games."))
        backup_active_live_button.connect('clicked',self._on_backup_active_live_button_clicked)
        self.actionbar.pack_start(backup_active_live_button)
        
        # Add a the search entry
        self.__search_entry = Gtk.Entry()
        self.__search_entry.set_hexpand(True)
        self.__search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY,'edit-find-symbolic')
        self.__search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,'edit-clear-symbolic')
        self.__search_entry.connect('icon-release',self._on_search_entry_icon_release)
        self.__search_entry.connect('changed',self._on_search_entry_changed)
        self.actionbar.pack_end(self.__search_entry)
        self.actionbar.pack_end(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        self.append(self.actionbar)
        
        self.__columnview = Gtk.ColumnView()
        columnview_sorter = self.columnview.get_sorter()
        self.__liststore = Gio.ListStore.new(GameViewData)
        
        gamemanager = GameManager.get_global()
        for g in gamemanager.games.values():
            self._liststore.append(GameViewData(g))
        self.__filter_model = Gtk.FilterListModel.new(self._liststore,None)
        self.__sort_model = Gtk.SortListModel.new(self.__filter_model,columnview_sorter)
            
        factory_icon = Gtk.SignalListItemFactory.new()
        factory_icon.connect('setup',self._on_icon_column_setup)
        factory_icon.connect('bind',self._on_icon_column_bind)
        column_icon = Gtk.ColumnViewColumn.new("",factory_icon)
        
        factory_key = Gtk.SignalListItemFactory.new()
        factory_key.connect('setup',self._on_key_column_setup)
        factory_key.connect('bind',self._on_key_column_bind)
        column_key = Gtk.ColumnViewColumn.new(_("Key"),factory_key)
        column_key.set_sorter(GameViewKeySorter())
        
        factory_name = Gtk.SignalListItemFactory.new()
        factory_name.connect('setup',self._on_name_column_setup)
        factory_name.connect('bind',self._on_name_column_bind)
        column_name = Gtk.ColumnViewColumn.new(_("Name"),factory_name)
        column_name.set_sorter(GameViewNameSorter())
        column_name.set_expand(True)
        
        factory_active = Gtk.SignalListItemFactory.new()
        factory_active.connect('setup',self._on_active_column_setup)
        factory_active.connect('bind',self._on_active_column_bind)
        factory_active.connect('unbind',self._on_active_column_unbind)
        column_active = Gtk.ColumnViewColumn.new(_("Active"),factory_active)
        
        factory_live = Gtk.SignalListItemFactory.new()
        factory_live.connect('setup',self._on_live_column_setup)
        factory_live.connect('bind',self._on_live_column_bind)
        factory_live.connect('unbind',self._on_live_column_unbind)
        column_live = Gtk.ColumnViewColumn.new(_("Live"),factory_live)
        
        factory_actions = Gtk.SignalListItemFactory.new()
        factory_actions.connect('setup',self._on_actions_column_setup)
        factory_actions.connect('bind',self._on_actions_column_bind)
        #factory_actions.connect('unbind',self._on_actions_column_unbind)
        column_actions = Gtk.ColumnViewColumn.new("",factory_actions)
        
        self.__selection_model = Gtk.SingleSelection(autoselect=False,can_unselect=True,model=self.__sort_model)
        
        self.columnview.set_vexpand(True)
        self.columnview.set_hexpand(True)
        self.columnview.set_single_click_activate(True)
        self.columnview.append_column(column_icon)
        self.columnview.append_column(column_key)
        self.columnview.append_column(column_name)
        self.columnview.append_column(column_active)
        self.columnview.append_column(column_live)
        self.columnview.append_column(column_actions)
        self.columnview.sort_by_column(column_name,Gtk.SortType.ASCENDING)
        self.columnview.set_model(self.__selection_model)
        
        
        cv_vadjustment = self.columnview.get_vadjustment()
        cv_vadjustment.set_value(cv_vadjustment.get_lower())
        scrolled.set_child(self.columnview)
        self.append(scrolled)
        
    @property
    def _liststore(self)->Gio.ListStore:
        """
        The `Gio.ListStore` that holds the list of registered games.
        
        :type: Gio.ListStore
        """
        return self.__liststore
    
    @property
    def columnview(self)->Gtk.ColumnView:
        """
        columnview The `Gtk.ColumnView` of the widget.

        :type: Gtk.ColumnView
        """
        return self.__columnview
    
    @property
    def actionbar(self)->Gtk.ActionBar:
        return self.__actionbar
    
    def refresh(self):
        """
        refresh Refresh the view.
        
        This method reloads the installed Games.
        """
        self.emit('refresh')
        
    @Signal(name="refresh",return_type=None,arg_types=(),flags=SignalFlags.RUN_FIRST)
    def do_refresh(self):
        self._liststore.remove_all()
        self.__search_entry.set_text("")
        
        gamemanager = GameManager.get_global()
        gamemanager.load()
        for game in gamemanager.games.values():
            self._liststore.append(GameViewData(game))
            
    def _on_game_dialog_response(self,dialog,response):
        if response == Gtk.ResponseType.APPLY:
            self.refresh()
            
    @Signal(name='game-active-changed',return_type=None,arg_types=(Game,),flags=SignalFlags.RUN_FIRST)
    def do_game_active_changed(self,game:Game):
        pass
    
    @Signal(name='game-live-changed',return_type=None,arg_types=(Game,),flags=SignalFlags.RUN_FIRST)
    def do_game_live_changed(self,game:Game):
        pass
    
    def _on_new_apps_dialog_response(self,dialog,response):
        self.refresh()
        
    def _on_add_game_button_clicked(self,button):
        dialog = GameDialog(parent=self.get_root())
        dialog.connect('response',self._on_game_dialog_response)
        dialog.present()
        
    def _on_new_steam_games_button_clicked(self,button):
        steam = Steam()
        if steam.find_new_steamapps():
            dialog = NewSteamAppsDialog(parent=self.get_root())
            dialog.connect_after('response',self._on_new_apps_dialog_response)
            dialog.present()
        else:
            dialog = SteamNoNewAppsDialog(parent=self.get_root())
            dialog.present()

    def _on_new_epic_games_button_clicked(self,button):
        epic = Epic()
        if not epic.find_new_apps():
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message="No new Epic-Games applications found!",
                buttons=Gtk.ButtonsType.OK,
                modal=False
            )
            dialog.connect('response',lambda d,r: d.destroy())
            dialog.present()
            return
        
        dialog = EpicNewAppsDialog(self.get_root())
        dialog.connect_after('response',self._on_new_apps_dialog_response)
        dialog.present()
    
    def _on_backup_active_live_button_clicked(self,button):
        backup_games = []
        for i in range(self._liststore.get_n_items()):
            game = self._liststore.get_item(i).game
            if game.is_live and game.is_active and os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
                backup_games.append(game)
         
 
        dialog =  BackupManyDialog(parent=self.get_root(),games=backup_games)
        dialog.set_modal(False)
        dialog.run()
        
    def __real_search(self,search_name:str):
        choices = []
        for i in range(self._liststore.get_n_items()):
            item = self._liststore.get_item(i)
            choices.append(item.name)
            item.fuzzy_match = 0.0
            
        result = rapidfuzz.process.extract(query=search_name,
                                           choices=choices,
                                           limit=settings.search_max_results,
                                           scorer=rapidfuzz.fuzz.WRatio)
        
        
        for name,match,pos in result:
            self._liststore.get_item(pos).fuzzy_match = match
        
        self.__filter_model.set_filter(GameViewMatchFilter())
        self.__sort_model.set_sorter(GameViewMatchSorter())
    
    def _on_search_entry_icon_release(self,entry,icon_pos):
        if icon_pos == Gtk.EntryIconPosition.PRIMARY:
            search_name=entry.get_text()
            if len(search_name) == 0:
                self.__filter_model.set_filter(None)
                self.__sort_model.set_sorter(self.columnview.get_sorter())
            else:
                self.__real_search(entry.get_text())
        elif icon_pos == Gtk.EntryIconPosition.SECONDARY:
            self.__search_entry.set_text("")
            self.__filter_model.set_filter(None)
            self.__sort_model.set_sorter(self.columnview.get_sorter())
    
    def _on_search_entry_changed(self,entry):
        search_name = entry.get_text()
        if len(search_name) == 0:
            self.__filter_model.set_filter(None)
            self.__sort_model.set_sorter(self.columnview.get_sorter())
        elif len(search_name) >= settings.search_min_chars:
            self.__real_search(search_name)
        
    def _on_icon_column_setup(self,factory,item):
        image = Gtk.Image()
        image.set_pixel_size(24)
        item.set_child(image)
        
    def _on_icon_column_bind(self,factory,item):
        def transform_to_icon_name(_binding,sgtype):
            icon_name = SAVEGAME_TYPE_ICONS[sgtype] if sgtype in SAVEGAME_TYPE_ICONS else ""
            if not icon_name:
                logger.warning(_("No icon-name for sgtype {}").format(sgtype.value))
            return icon_name
            
        icon = item.get_child()
        game = item.get_item().game
        
        icon.props.icon_name = transform_to_icon_name(None,game.savegame_type)
        
        if not hasattr(game,'_savegame_type_to_icon_name_binding'):
            game._savegame_type_to_icon_name_binding = game.bind_property('savegame_type',icon,'icon_name',BindingFlags.DEFAULT,transform_to_icon_name)        
        
    def _on_key_column_setup(self,factory,item):
        label = Gtk.Label()
        label.set_xalign(0.0)
        label.set_use_markup(True)
        item.set_child(label)
        
    def _on_key_column_bind(self,factory,item):
        label = item.get_child()
        game = item.get_item().game
        game.bind_property('key',label,'label',BindingFlags.SYNC_CREATE,
                           lambda _binding,s: '<span size="large">{}</span>'.format(GLib.markup_escape_text(s)))
        
    def _on_name_column_setup(self,factory,item):
        label = Gtk.Label()
        label.set_xalign(0.0)
        label.set_use_markup(True)
        item.set_child(label)
        
    def _on_name_column_bind(self,factory,item):
        label = item.get_child()
        game = item.get_item().game
        if not hasattr(label,'_property_label_from_name_binding'):
            label._property_label_from_name_binding = game.bind_property('name',
                                                                         label,
                                                                         'label',
                                                                         BindingFlags.SYNC_CREATE,
                                                                         lambda _binding,s: "<span weight='bold' size='large'>{}</span>".format(
                                                                             GLib.markup_escape_text(s)))

    def _on_active_column_setup(self,factory,item):
        item.set_child(Gtk.Switch())
        
    def _on_active_column_bind(self,factory,item):
        switch = item.get_child()
        game = item.get_item().game
        switch.set_active(game.is_active)
        item._signal_active_state_set = switch.connect('state-set',self._on_active_state_set,game)
        
    def _on_active_column_unbind(self,factory,item):
        if hasattr(item,'_signal_active_state_set'):
            item.get_child().disconnect(item._signal_active_state_set)
            del item._signal_active_state_set
        
    def _on_active_state_set(self,switch,state,game):
        game.is_active = switch.get_active()
        game.save()
        self.emit('game-active-changed',game)
        
    def _on_live_column_setup(self,factory,item):
        item.set_child(Gtk.Switch())
        
    def _on_live_column_bind(self,factory,item):
        switch = item.get_child()
        game = item.get_item().game
        switch.set_active(game.is_live)
        if not hasattr(item,'_signal_live_state_set'):
            item._signal_live_state_set = switch.connect('state-set',self._on_live_state_set,game)
        
    def _on_live_column_unbind(self,factory,item):
        if hasattr(item,'_signal_live_state_set'):
            item.get_child().disconnect(item._signal_live_state_set)
            del item._signal_live_state_set
        
    def _on_live_state_set(self,switch,state,game):
        def on_dialog_response(dialog,response):
            dialog.hide()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                dialog = BackupSingleDialog(parent=self.get_root(),game=game)
                dialog.run()
            
        game.is_live = switch.get_active()
        game.save()
        if not game.is_live:
            dialog = Gtk.MessageDialog(buttons=Gtk.ButtonsType.YES_NO)
            dialog.set_transient_for(self.get_root())
            dialog.props.text = _("Do you want to create a new savegame for <i>{game}</i>?").format(game=game.name)
            dialog.props.use_markup = True
            dialog.props.secondary_text = _("The new savegame is added to the finsihed savegames for the game.")
            dialog.props.secondary_use_markup = False
            dialog.connect('response',on_dialog_response)
            dialog.present()
        self.emit('game-live-changed',game)
    
    def _on_actions_column_setup(self,action,item):
        child = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,2)
        
        icon = Gtk.Image.new_from_icon_name('document-save-symbolic')
        child.backup_button = Gtk.Button()
        child.backup_button.set_child(icon)
        child.backup_button.set_tooltip_text(_("Backup the SaveGames for this game."))
        child.append(child.backup_button)
        
        icon = Gtk.Image.new_from_icon_name('document-edit-symbolic')
        child.edit_button = Gtk.Button()
        child.edit_button.set_child(icon)
        child.edit_button.set_tooltip_text('Edit this game.')
        child.append(child.edit_button)
        
        icon = Gtk.Image.new_from_icon_name('list-remove-symbolic')
        child.remove_button = Gtk.Button()
        child.remove_button.set_child(icon)
        child.remove_button.set_tooltip_markup(_("Remove this game.\n<span weight='ultrabold'>This also deletes the game configuration file!!!</span>"))
        child.append(child.remove_button)
        
        item.set_child(child)
        
    def _on_actions_column_bind(self,action,item):
        child = item.get_child()
        game = item.get_item().game
        archiver_manager = ArchiverManager.get_global()
        
        # check if we are already connected.
        # if we dont check we might have more than one dialog open or execute backups more than once 
        # due to Gtk4 reusing the widgets. When selecting a row in the columnview this method is called.
        if hasattr(child.backup_button,'_signal_clicked_connection'):
            child.backup_button.disconnect(child.backup_button._signal_clicked_connection)
        child.backup_button._signal_clicked_connection = child.backup_button.connect('clicked',self._on_columnview_backup_button_clicked,item)
        
        if not hasattr(child.backup_button,'_property_backup_in_progress_binding'):
            child.backup_button._property_backup_in_progress_binding = archiver_manager.bind_property('backup-in-progress',
                                                                                                      child.backup_button,
                                                                                                      'sensitive',
                                                                                                      BindingFlags.SYNC_CREATE,
                                                                                                      lambda binding,x: False if x else True)
            
        if hasattr(child.edit_button,'_signal_clicked_connection'):
            child.edit_button.disconnect(child.edit_button._signal_clicked_connection)
        child.edit_button._signal_clicked_connection = child.edit_button.connect('clicked',self._on_columnview_edit_button_clicked,item)
            
        if not hasattr(child.edit_button,'_property_backup_in_progress_binding'):
            child.edit_button._property_backup_in_progress_binding = archiver_manager.bind_property('backup-in-progress',
                                                                                                    child.edit_button,
                                                                                                    'sensitive',
                                                                                                    BindingFlags.SYNC_CREATE,
                                                                                                    lambda binding,x: False if x else True)
            
        if hasattr(child.remove_button,'_signal_clicked_connection'):
            child.remove_button.disconnect(child.remove_button._signal_clicked_connection)
        child.remove_button._signal_clicked_connection = child.remove_button.connect('clicked',self._on_columnview_remove_button_clicked,item)
        
        if not hasattr(child.remove_button,'_property_backup_in_progress_binding'):
            child.remove_button._property_backup_in_progress_binding = archiver_manager.bind_property('backup-in-progress',
                                                                                                      child.remove_button,'sensitive',
                                                                                                      BindingFlags.SYNC_CREATE,
                                                                                                      lambda binding,x: False if x else True)
        
        
        if os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
            child.backup_button.set_sensitive(True)
        else:
            child.backup_button.set_sensitive(False)
            
    def _on_columnview_backup_button_clicked(self,button,item):
        def on_dialog_response(self,dialog,parent):
            if hasattr(parent,'statusbar'):
                parent.statusbar.pop(1)
                
        game = item.get_item().game
        parent = self.get_root()
        dialog = BackupSingleDialog(parent,game)
        
        if hasattr(parent,'statusbar'):
            parent.statusbar.push(1,"Backing up \"{game}\" ...".format(game=game.name))
        dialog.connect('response',on_dialog_response,parent)
        dialog.run()
    
    def _on_columnview_edit_button_clicked(self,button,item):
        def on_dialog_response(dialog,response):
            if response == Gtk.ResponseType.APPLY:
                self.refresh()
        
        game = item.get_item().game
        
        dialog = GameDialog(self.get_root(),game)
        dialog.set_modal(False)
        dialog.connect_after('response',on_dialog_response)
        dialog.present()
        
        
    def _on_columnview_remove_button_clicked(self,button,item):
        def on_dialog_response(dialog,response,game:Game):
            if response == Gtk.ResponseType.YES:
                if os.path.isfile(game.filename):
                    os.unlink(game.filename)
                for i in range(self._liststore.get_n_items()):
                    item = self._liststore.get_item(i)
                    if item.key == game.key:
                        self._liststore.remove(i)
                        break
                   
            dialog.hide()
            dialog.destroy()
            
        game = item.get_item().game
        dialog = Gtk.MessageDialog(buttons=Gtk.ButtonsType.YES_NO,
                                   text=_("Do you really want to remove the game <span weight='bold'>{game}</span>?").format(
                                   game=game.name),
                                   use_markup=True,
                                   secondary_text=_("Removing games cannot be undone!!!"))
        dialog.set_transient_for(self.get_root())
        dialog.set_modal(False)
        dialog.connect('response',on_dialog_response,game)
        dialog.present()
# GameView class

class BackupViewData(GObject):
    """
    BackupViewData The data class for BackupView
    """
    
    def __init__(self,_game:Game,filename:str):
        GObject.__init__(self)
        self.__game = _game
        self.__filename = filename
        
        basename = os.path.basename(filename)
        parts = basename.split('.')
        
        try:
            self.__savegame_name = parts[0]
            self.__timestamp = DateTime.strptime(parts[1],"%Y%m%d-%H%M%S")
            self.__sgtype = SavegameType.from_string(parts[2])
            self.__is_live = parts[3] == 'live'
        except:
            self.__savegame_name = basename
            self.__timestamp = "Unknown"
            self.__sgtype = SavegameType.UNSET
            self.__is_live = True
        
            
        WINDOWS_TYPES = [
            SavegameType.WINDOWS,
            SavegameType.STEAM_WINDOWS,
            SavegameType.EPIC_WINDOWS,
            SavegameType.GOG_WINDOWS,
        ]
        LINUX_TYPES = [
            SavegameType.LINUX,
            SavegameType.STEAM_LINUX,
            SavegameType.EPIC_LINUX,
            SavegameType.GOG_LINUX,
        ]
        MACOS_TYPES = [
            SavegameType.MACOS,
            SavegameType.STEAM_MACOS,
        ]
        
        if self.__sgtype in WINDOWS_TYPES:
            self.__sgos = 'windows'
        elif self.__sgtype in LINUX_TYPES:
            self.__sgos = 'linux'
        elif self.__sgtype in MACOS_TYPES:
            self.__sgos = 'macos'
        else:
            self.__sgos = ''
            
        self.__extension = '.' + '.'.join(parts[5:])
        
    
    @property
    def game(self)->Game:
        """
        game The `Game` the data belong to

        :type: Game
        """
        return self.__game
    
    @Property
    def savegame_type(self)->SavegameType:
        return self.__sgtype
    
    @Property(type=str)
    def savegame_type_icon_name(self)->str:
        return SAVEGAME_TYPE_ICONS[self.__sgtype]
    
    @Property(type=str)
    def savegame_os(self)->str:
        return self.__sgos
    
    @Property(type=bool,default=False)
    def savegame_os_is_host_os(self):
        platform = "unknown"
        if (sys.platform.lower().startswith('win')):
            platform = 'windows'
        elif (sys.platform.lower() == 'macos'):
            paltform = 'macos'
        elif (sys.platform.lower() in ('linux','freebsd','netbsd','openbsd','dragonfly')):
            platform = 'linux'
            
        return (self.savegame_os == platform)
        
    @Property(type=str)
    def savegame_os_icon_name(self)->str:
        if self.__sgos:
            return SAVEGAME_TYPE_ICONS[self.__sgos]
        return ""
    
    
    @Property(type=str)
    def savegame_name(self)->str:
        """
        savegame_name The savegame_name of the file.

        :type: str
        """
        return self.__savegame_name
    
    @Property(type=str)
    def filename(self)->str:
        """
        filename The full filename of the savegame backup.

        :type: str
        """
        return self.__filename
    
    @Property(type=bool,default=False)
    def is_live(self)->bool:
        """
        is_live `True` if the savegame backup is from a live game.

        :type: bool
        """
        return self.__is_live
    
    @Property(type=str)
    def extension(self)->str:
        """
        extension The extension of the file.

        :type: str
        """
        return self.__extension
    
    @Property
    def timestamp(self)->DateTime:
        """
        timestamp The timestamp of the file.
        
        DateTime is the alias for `datetime.datetime`.

        :type: DateTime
        """
        return self.__timestamp
    

class BackupViewSorter(Gtk.Sorter):
    def do_compare(self,item1:BackupViewData,item2:BackupViewData):
        if (item1.timestamp < item2.timestamp):
            return Gtk.Ordering.LARGER
        elif (item1.timestamp > item2.timestamp):
            return Gtk.Ordering.SMALLER
        else:
            return Gtk.Ordering.EQUAL
class BackupView(Gtk.Box):
    """
    BackupView This view displays the backup for the selected `Game`.
    """
    __gtype_name__ = "BackupView"
    def __init__(self,gameview:GameView):
        """
        BackupView

        :param gameview: The `GameView` to connect this class to.
        :type gameview: GameView
        """
        Gtk.Box.__init__(self,orientation=Gtk.Orientation.VERTICAL)
        self._title_label = Gtk.Label()
        scrolled = Gtk.ScrolledWindow()
        self.__gameview = gameview
        
        self.__action_group = Gio.SimpleActionGroup.new()
        self.__create_actions()
        self.insert_action_group("backupview",self.action_group)
        
        self.__liststore = Gio.ListStore()
        sort_model = Gtk.SortListModel(model=self.__liststore,sorter=BackupViewSorter())
        self.__selection_model = Gtk.SingleSelection(model=sort_model,
                                                     autoselect=False,
                                                     can_unselect=True)
        self.__selection_model.connect('selection-changed',self._on_columnview_selection_changed)
        
        sgtype_factory = Gtk.SignalListItemFactory()
        sgtype_factory.connect('setup',self._on_sgtype_column_setup)
        sgtype_factory.connect('bind',self._on_sgtype_column_bind)
        sgtype_column = Gtk.ColumnViewColumn.new("",sgtype_factory)
        
        sgos_factory = Gtk.SignalListItemFactory()
        sgos_factory.connect('setup',self._on_sgos_column_setup)
        sgos_factory.connect('bind',self._on_sgos_column_bind)
        sgos_column = Gtk.ColumnViewColumn.new(_("OS"),sgos_factory)
        
        live_factory = Gtk.SignalListItemFactory()
        live_factory.connect('setup',self._on_live_column_setup)
        live_factory.connect('bind',self._on_live_column_bind)
        live_column = Gtk.ColumnViewColumn.new(_("Live"),live_factory)
        
        sgname_factory = Gtk.SignalListItemFactory()
        sgname_factory.connect('setup',self._on_savegamename_column_setup)
        sgname_factory.connect('bind',self._on_savegamename_column_bind)
        sgname_column = Gtk.ColumnViewColumn.new(_("Savegame name"),sgname_factory)
        sgname_column.set_expand(True)
        
        timestamp_factory = Gtk.SignalListItemFactory()
        timestamp_factory.connect('setup',self._on_timestamp_column_setup)
        timestamp_factory.connect('bind',self._on_timestamp_column_bind)
        timestamp_column = Gtk.ColumnViewColumn.new(_("Timestamp"),timestamp_factory)
        
        size_factory = Gtk.SignalListItemFactory()
        size_factory.connect('setup',self._on_size_column_setup)
        size_factory.connect('bind',self._on_size_column_bind)
        size_column = Gtk.ColumnViewColumn.new(_("Size"),size_factory)
        
        actions_factory = Gtk.SignalListItemFactory()
        actions_factory.connect('setup',self._on_actions_column_setup)
        actions_factory.connect('bind',self._on_actions_column_bind)
        actions_column = Gtk.ColumnViewColumn.new("",actions_factory)
        
        self.__columnview = Gtk.ColumnView.new(self.__selection_model)
        self.__columnview.append_column(sgtype_column)
        self.__columnview.append_column(sgos_column)
        self.__columnview.append_column(live_column)
        self.__columnview.append_column(sgname_column)
        self.__columnview.append_column(timestamp_column)
        self.__columnview.append_column(size_column)
        self.__columnview.append_column(actions_column)
        self.__columnview.set_vexpand(True)
        self.__columnview.set_single_click_activate(True)
        
        self.gameview.columnview.connect('activate',self._on_gameview_columnview_activate)
        
        scrolled.set_child(self.__columnview)
        
        self.append(self._title_label)
        self.append(scrolled)
        
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__),'appmenu.ui'))
        builder.set_translation_domain(TEXTDOMAIN)
        
        self.__convertmenu = builder.get_object('backupview-convert-menu')
                
    @property
    def gameview(self)->GameView:
        """
        gameview The GameView this class is connected to.

        :type: GameView
        """
        return self.__gameview
    
    @property
    def action_group(self)->Gio.SimpleActionGroup:
        return self.__action_group

    def __create_actions(self):
        self.__restore_action = Gio.SimpleAction.new("restore",None)
        self.__restore_action.connect('activate',self._on_action_restore)
        self.action_group.add_action(self.__restore_action)
        
        self.__convert_to_windows_action = Gio.SimpleAction.new("convert-to-windows",None)
        self.__convert_to_windows_action.connect('activate',self._on_action_convert_to_windows)
        self.action_group.add_action(self.__convert_to_windows_action)
        
        self.__convert_to_linux_action = Gio.SimpleAction.new("convert-to-linux",None)
        self.__convert_to_linux_action.connect('activate',self._on_action_convert_to_linux)
        self.action_group.add_action(self.__convert_to_linux_action)
        
        self.__convert_to_macos_action = Gio.SimpleAction.new("convert-to-macos",None)
        self.__convert_to_macos_action.connect('activate',self._on_action_convert_to_macos)
        self.action_group.add_action(self.__convert_to_macos_action)
        
        self.__convert_to_epic_linux_action = Gio.SimpleAction.new("convert-to-epic-linux",None)
        self.__convert_to_epic_linux_action.connect('activate',self._on_action_convert_to_epic_linux)
        self.action_group.add_action(self.__convert_to_epic_linux_action)
        
        self.__convert_to_epic_windows_action = Gio.SimpleAction.new("convert-to-epic-windows",None)
        self.__convert_to_epic_windows_action.connect('activate',self._on_action_convert_to_epic_windows)
        self.action_group.add_action(self.__convert_to_epic_windows_action)
        
        self.__convert_to_gog_linux_action = Gio.SimpleAction.new("convert-to-gog-linux",None)
        self.__convert_to_gog_linux_action.connect('activate',self._on_action_convert_to_gog_linux)
        self.action_group.add_action(self.__convert_to_gog_linux_action)
        
        self.__convert_to_gog_windows_action = Gio.SimpleAction.new("convert-to-gog-windows",None)
        self.__convert_to_gog_windows_action.connect('activate',self._on_action_convert_to_gog_windows)
        self.action_group.add_action(self.__convert_to_gog_windows_action)
        
        self.__convert_to_steam_linux_action = Gio.SimpleAction.new("convert-to-steam-linux",None)
        self.__convert_to_steam_linux_action.connect('activate',self._on_action_convert_to_steam_linux)
        self.action_group.add_action(self.__convert_to_steam_linux_action)
        
        self.__convert_to_steam_macos_action = Gio.SimpleAction.new("convert-to-steam-macos",None)
        self.__convert_to_steam_macos_action.connect('activate',self._on_action_convert_to_steam_macos)
        self.action_group.add_action(self.__convert_to_steam_macos_action)
        
        self.__convert_to_steam_windows_action = Gio.SimpleAction.new("convert-to-steam-windows",None)
        self.__convert_to_steam_windows_action.connect('activate',self._on_action_convert_to_steam_windows)
        self.action_group.add_action(self.__convert_to_steam_windows_action)
        
    def _on_action_restore(self,action,param):
        pass
    
    def _on_action_convert_to_windows(self,action,param):
        pass
    
    def _on_action_convert_to_linux(self,action,param):
        pass
    
    def _on_action_convert_to_macos(self,action,param):
        pass
    
    def _on_action_convert_to_steam_windows(self,action,param):
        pass
    
    def _on_action_convert_to_steam_linux(self,action,param):
        pass
    
    def _on_action_convert_to_steam_macos(self,action,param):
        pass
    
    def _on_action_convert_to_epic_windows(self,action,param):
        pass
    
    def _on_action_convert_to_epic_linux(self,action,param):
        pass
    
    def _on_action_convert_to_gog_windows(self,action_param):
        pass
    
    def _on_action_convert_to_gog_linux(self,action,param):
        pass
    
    def _on_columnview_selection_changed(self,selection,position,n_items):
        data = selection.get_selected_item()
        
        #######################################################################
        #TODO: implement converter
        self.__convert_to_linux_action.set_enabled(False)
        self.__convert_to_macos_action.set_enabled(False)
        self.__convert_to_windows_action.set_enabled(False)
        self.__convert_to_epic_linux_action.set_enabled(False)
        self.__convert_to_epic_windows_action.set_enabled(False)
        self.__convert_to_gog_linux_action.set_enabled(False)
        self.__convert_to_gog_windows_action.set_enabled(False)
        self.__convert_to_steam_linux_action.set_enabled(False)
        self.__convert_to_steam_macos_action.set_enabled(False)
        self.__convert_to_steam_windows_action.set_enabled(False)
        #######################################################################
    
    def _on_sgtype_column_setup(self,factory,item):
        icon = Gtk.Image()
        icon.set_pixel_size(24)
        item.set_child(icon)
        
    def _on_sgtype_column_bind(self,factory,item):
        icon = item.get_child()
        data = item.get_item()
        icon.set_from_icon_name(data.savegame_type_icon_name)
        
    def _on_sgos_column_setup(self,factory,item):
        icon = Gtk.Image()
        icon.set_pixel_size(24)
        item.set_child(icon)
        
    def _on_sgos_column_bind(self,factory,item):
        icon = item.get_child()
        data = item.get_item()
        if data.savegame_os_icon_name:
            icon.set_from_icon_name(data.savegame_os_icon_name)
        
    def _on_live_column_setup(self,factory,item):
        checkbutton = Gtk.CheckButton()
        checkbutton.set_sensitive(False)
        item.set_child(checkbutton)
        
    def _on_live_column_bind(self,factory,item):
        checkbutton = item.get_child()
        data = item.get_item()
        checkbutton.set_active(data.is_live)
    
    def _on_savegamename_column_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_savegamename_column_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_markup("<span size=\"large\">{}</span>".format(
            GLib.markup_escape_text(data.savegame_name)))
        
    def _on_timestamp_column_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_timestamp_column_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_markup("<span size=\"large\">{}</span>".format(
            GLib.markup_escape_text(data.timestamp.strftime(_("%m.%d.%Y %H:%M:%S")))))
        
    def _on_size_column_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_size_column_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        file = Path(data.filename).resolve()

        if not file.is_file():
            label.set_markup("<span size=\"large\">0 B</span>")
            return
        
        size = file.stat().st_size
        if (size > 1073741824):
            display_size = ".".join((str(int(size / 1073741824)),str(int(((size * 10) / 1073741824) % 10)))) + " GiB"
        elif (size > 1048576):
            display_size = ".".join((str(int(size / 1048576)), str(int(((size * 10) / 1048576) % 10)))) + " MiB"
        elif (size > 1024):
            display_size = ".".join((str(int(size / 1024)), str(int(((size * 10) / 1024) % 10)))) + " KiB"
        else:
            display_size = str(size) + " B"
        label.set_markup("<span size=\"large\">{}</span>".format(
            GLib.markup_escape_text(display_size)))
        
    def _on_actions_column_setup(self,factory,item):
        child = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,2)
        child.restore_button = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name('document-revert-symbolic')
        icon.set_pixel_size(16)
        child.restore_button.set_child(icon)
        child.restore_button.set_tooltip_text(_("Restore the SaveGameBackup."))
        child.append(child.restore_button)
        
        child.convert_button = Gtk.MenuButton()
        child.convert_button.set_icon_name('document-properties-symbolic')
        child.convert_button.set_tooltip_text(_("Convert to another SaveGameBackup."))
        child.convert_button.set_menu_model(self.__convertmenu)
        child.convert_button.set_direction(Gtk.ArrowType.UP)
        child.append(child.convert_button)
        
        child.delete_button = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name('list-remove-symbolic')
        icon.set_pixel_size(16)
        child.delete_button.set_child(icon)
        child.delete_button.set_tooltip_text(_("Delete this SaveGameBackup."))
        child.append(child.delete_button)
        
        item.set_child(child)
        
    def _on_actions_column_bind(self,factory,item):
        child = item.get_child()
        data = item.get_item()
        
        if hasattr(child.restore_button,'_signal_clicked_connector'):
            child.restore_button.disconnect(child.restore_button._signal_clicked_connector)
            del child.restore_button._signal_clicked_connector
        if hasattr(child.delete_button,'_signal_clicked_connector'):
            child.delete_button.disconnect(child.delete_button._signal_clicked_connector)
            del child.delete_button._signal_clicked_connector
        child.restore_button._signal_clicked_connector = child.restore_button.connect('clicked',self._on_restore_button_clicked,data)
        child.delete_button._signal_clicked_connector = child.delete_button.connect('clicked',self._on_delete_button_clicked,data)
        
        
    def _on_restore_button_clicked(self,button,data:BackupViewData):
        pass
    
    def _on_delete_button_clicked(self,button,data:BackupViewData):
        am = ArchiverManager.get_global()
        am.remove_backup(data.game,data.filename)
        for i in range(self.__liststore.get_n_items()):
            item = self.__liststore.get_item(i)
            if (item.filename == data.filename):
                self.__liststore.remove(i)
                return
        
    def _on_gameview_columnview_activate(self,columnview,position):
        model = columnview.get_model().get_model()
        game = model.get_item(position).game
        
        self._title_label.set_markup("<span size='large' weight='bold'>{}</span>".format(GLib.markup_escape_text(game.name)))
        
        self.__liststore.remove_all()
        for bf in sorted(ArchiverManager.get_global().get_backups(game),reverse=True):
            try:
                self.__liststore.append(BackupViewData(game,bf))
            except: 
                pass
        

class AppWindow(Gtk.ApplicationWindow):
    """
    AppWindow The applications main window.
    """
    __gtype_name__ = "AppWindow"
    def __init__(self,application=None,**kwargs):
        """
        AppWindow

        :param application: The `Application` this window belongs to, defaults to `None`.
        :type application: Application, optional
        """
        kwargs['title'] = _("SGBackup")
        
        if (application is not None):
            kwargs['application']=application
            if (hasattr(application,'builder')):
                builder = application.builder
            else:
                builder = Gtk.Builder.new()
                
        Gtk.ApplicationWindow.__init__(self,**kwargs)
        self.set_default_size(800,700)
        self.set_icon_name('org.sgbackup.sgbackup-symbolic')
        
        self.__builder = builder
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__),'appmenu.ui'))
        gmenu = self.builder.get_object('appmenu')
        appmenu_popover = Gtk.PopoverMenu.new_from_model(gmenu)
        image = Gtk.Image.new_from_icon_name('open-menu-symbolic')
        menubutton = Gtk.MenuButton.new()
        menubutton.set_popover(appmenu_popover)
        menubutton.set_child(image)
        headerbar = Gtk.HeaderBar.new()
        headerbar.pack_start(menubutton)
        self.set_titlebar(headerbar)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        self.__vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.__vpaned.set_hexpand(True)
        self.__vpaned.set_vexpand(True)
        self.__vpaned.set_wide_handle(True)
        self.__gameview = GameView()
        self.__vpaned.set_start_child(self.gameview)
        self.__backupview = BackupView(self.gameview)
        self.__vpaned.set_end_child(self.backupview)
        self.__vpaned.set_resize_start_child(True)
        self.__vpaned.set_resize_end_child(True)
        self.__vpaned.set_position(400)
        
        vbox.append(self.__vpaned)
        
        self.__statusbar = Gtk.Statusbar()
        self.statusbar.set_hexpand(True)
        self.statusbar.set_vexpand(False)
        self.gameview.connect('refresh',self._on_gameview_refresh)
        self.gameview.connect('game-active-changed',lambda gv,*data: self._on_gameview_refresh(gv))
        self.gameview.connect('game-live-changed',lambda gv,*data: self._on_gameview_refresh(gv))
        
        n_games = self.gameview._liststore.get_n_items()
        n_live = 0
        n_active = 0
        n_finished = 0
        for i in range(n_games):
            game = self.gameview._liststore.get_item(i).game
            if game.is_live:
                n_live += 1
            else:
                n_finished += 1
    
            if  game.is_active:
                n_active += 1
            
        self.statusbar.push(0,_('{games} Games -- {active} Games active -- {live} Games live -- {finished} Games finished').format(
            games=n_games,
            active=n_active,
            live=n_live,
            finished=n_finished))
        
        vbox.append(self.statusbar)
        
        self.set_child(vbox)
        
    @property
    def builder(self)->Gtk.Builder:
        """
        builder The Builder for this Window.

        If application is set and it has an attriubte *builder*, The applications builder 
        is used else a new `Gtk.Builder` instance is created.
        
        :type: Gtk.Builder
        """
        return self.__builder

    @property
    def backupview(self)->BackupView:
        """
        backupview The `BackupView` of this window.

        :type: BackupView
        """
        return self.__backupview
    
    @property
    def gameview(self)->GameView:
        """
        gameview The `GameView` for this window.

        :type: GameView
        """
        return self.__gameview
    
    @property
    def statusbar(self):
        return self.__statusbar
    
    def refresh(self,reload_game_manager:bool=False):
        """
        refresh Refresh the views of this window.
        """
        if reload_game_manager:
            GameManager.get_global().load()
        self.gameview.refresh()
        #self.backupview.refresh()
        
    def _on_gameview_refresh(self,gameview):
        self.statusbar.pop(0)
        n_games = gameview._liststore.get_n_items()
        n_active = 0
        n_live = 0
        n_finished = 0
        for i in range(n_games):
            game = gameview._liststore.get_item(i).game
            if game.is_live:
                n_live += 1
            else:
                n_finished += 1
    
            if  game.is_active:
                n_active += 1
            
        self.statusbar.push(0,_('{games} Games -- {active} Games active -- {live} Games live -- {finished} Games finished').format(
            games=n_games,
            active=n_active,
            live=n_live,
            finished=n_finished))
        
            
class Application(Gtk.Application):
    """
    Application The `Gtk.Application` for this app.
    
    Signals
    _______
    
    + **settings-dialog-init** - Called when the application creates a new `SettingsDialog`.
    """
    __gtype_name__ = "Application"
    
    def __init__(self,*args,**kwargs):
        """
        Application
        """
        AppFlags = Gio.ApplicationFlags
        kwargs['application_id'] = 'org.sgbackup.sgbackup'
        kwargs['flags'] = AppFlags.FLAGS_NONE
        Gtk.Application.__init__(self,*args,**kwargs)
        
        self.__logger = logger.getChild('Application')
        self.__builder = None   
        self.__appwindow = None
        
    @property
    def _logger(self):
        return self.__logger
    
    @property
    def appwindow(self)->AppWindow:
        """
        appwindow The main `AppWindow` of this app.

        :type: AppWindow
        """
        return self.__appwindow
    
    def do_startup(self):
        """
        do_startup The startup method for this application.
        """
        self._logger.debug('do_startup()')
        if not self.__builder:
            self.__builder = Gtk.Builder.new()
            self.__builder.set_translation_domain(TEXTDOMAIN)
        Gtk.Application.do_startup(self)
        
        pkg_path = Path(__file__).resolve()
        pkg_path = pkg_path.parent.parent
        icons_path = pkg_path / "icons"
        
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        #theme.add_resource_path("/org/sgbackup/sgbackup/icons")
        theme.add_search_path(str(icons_path))
        
        action_about = Gio.SimpleAction.new('about',None)
        action_about.connect('activate',self._on_action_about)
        self.add_action(action_about)
        
        action_help = Gio.SimpleAction.new('help',None)
        action_help.connect('activate',self._on_action_help)
        self.add_action(action_help)
        
        action_backup_all = Gio.SimpleAction.new('backup-all',None)
        action_backup_all.connect('activate',self._on_action_backup_all)
        self.add_action(action_backup_all)
        
        action_backup_active_live = Gio.SimpleAction.new('backup-active-live',None)
        action_backup_active_live.connect('activate',self._on_action_backup_active_live)
        self.add_action(action_backup_active_live)
        
        action_new_game = Gio.SimpleAction.new('new-game',None)
        action_new_game.connect('activate',self._on_action_new_game)
        self.add_action(action_new_game)
        
        action_quit = Gio.SimpleAction.new('quit',None)
        action_quit.connect('activate',self._on_action_quit)
        self.add_action(action_quit)
                
        action_settings = Gio.SimpleAction.new('settings',None)
        action_settings.connect('activate',self._on_action_settings)
        self.add_action(action_settings)
        
        action_steam_manage_libraries = Gio.SimpleAction.new('steam-manage-libraries',None)
        action_steam_manage_libraries.connect('activate',self._on_action_steam_manage_libraries)
        self.add_action(action_steam_manage_libraries)
        
        action_steam_new_apps = Gio.SimpleAction.new('steam-new-apps',None)
        action_steam_new_apps.connect('activate',self._on_action_steam_new_apps)
        self.add_action(action_steam_new_apps)
        
        action_steam_manage_ignore = Gio.SimpleAction.new('steam-manage-ignore',None)
        action_steam_manage_ignore.connect('activate',self._on_action_steam_manage_ignore)
        self.add_action(action_steam_manage_ignore)
        
        # add accels
        self.set_accels_for_action('app.quit',["<Primary>q"])
        self.set_accels_for_action('app.backup-all',["<Primary><Shift>s"])
        self.set_accels_for_action('app.backup-active-live',["<Primary>s"])
        
    @property
    def builder(self)->Gtk.Builder:
        """
        builder Get the builder for the application.

        :type: Gtk.Builder
        """
        return self.__builder
    
    def do_activate(self):
        """
        do_activate This method is called, when the application is activated.
        """
        self._logger.debug('do_activate()')
        if not (self.__appwindow):
            self.__appwindow = AppWindow(application=self)
            
        
        self.appwindow.present()
        
    def _on_action_about(self,action,param):
        dialog = AboutDialog()
        dialog.present()
    
    def _on_action_help(self,action,param):
        #TODO
        uri = Gtk.UriLauncher.new("https://sgbackup.org")
        uri.launch(self.appwindow,None,None)
    
    def _on_action_settings(self,action,param):
        dialog = self.new_settings_dialog()
        dialog.present()
    
    def _on_action_quit(self,action,param):
        self.quit()
        
    def _on_action_new_game(self,action,param):
        def on_dialog_apply(dialog):
            self.appwindow.refresh()
                
        dialog = GameDialog(self.appwindow)
        dialog.connect('apply',on_dialog_apply)
        dialog.present()

    def _on_action_backup_active_live(self,action,param):
        gamemanager = GameManager.get_global()
        
        if not gamemanager.games:
            dialog=NoGamesToBackupDialog(self.appwindow)
            dialog.present()
            return
        
        games = [g for g in gamemanager.games.values() 
                 if (g.is_active 
                     and g.is_live
                     and os.path.exists(os.path.join(g.savegame_root,g.savegame_dir)))]
        if games:
            if len(games) == 1:
                dialog = BackupSingleDialog(self.appwindow,games[0])
            else:
                dialog = BackupManyDialog(self.appwindow,games)
            dialog.run()
        else:
            dialog = NoGamesToBackupFoundDialog(self.appwindow)
            dialog.present()
    
    def _on_action_backup_all(self,action,param):
        gamemanager = GameManager.get_global()
        
        if not gamemanager.games:
            dialog=NoGamesToBackupDialog(self.appwindow)
            dialog.present()
            return
        
        games = [g for g in gamemanager.games.values() 
                 if os.path.exists(os.path.join(g.savegame_root,g.savegame_dir))]
        if games:
            if len(games) == 1:
                dialog = BackupSingleDialog(self.appwindow,games[0])
            else:
                dialog = BackupManyDialog(self.appwindow,games)
            dialog.run()
        else:
            dialog = NoGamesToBackupFoundDialog(self.appwindow)
            dialog.present()
    
    def _on_action_steam_manage_libraries(self,action,param):
        dialog = SteamLibrariesDialog(self.appwindow)
        dialog.present()
        
    def _on_action_steam_new_apps(self,action,param):
        def on_dialog_response(dialog,response):
            self.appwindow.refresh()
            
        steam = Steam()
        if steam.find_new_steamapps():
            dialog = NewSteamAppsDialog(self.appwindow)
            dialog.connect_after('response',on_dialog_response)
            dialog.present()
        else:
            dialog = SteamNoNewAppsDialog(self.appwindow)
            dialog.present()

        
    def _on_action_steam_manage_ignore(self,action,param):
        steam = Steam()
        if not steam.ignore_apps:
            dialog = SteamNoIgnoredAppsDialog(self.appwindow)
        else:
            dialog = SteamIgnoreAppsDialog(self.appwindow)
            dialog.connect_after("response",lambda d,r:self.appwindow.refresh())
            
        dialog.present()
        
    def new_settings_dialog(self)->SettingsDialog:
        """
        new_settings_dialog Create a new `SettingsDialog`.

        :return: The new dialog.
        :rtype: `SettingsDialog`
        """
        dialog = SettingsDialog(self.appwindow)
        self.emit('settings-dialog-init',dialog)
        return dialog
        
    @Signal(name='settings-dialog-init',
            flags=SignalFlags.RUN_LAST,
            return_type=None,
            arg_types=(SettingsDialog,))
    def do_settings_dialog_init(self,dialog:SettingsDialog):
        """
        do_settings_dialog_init The **settings-dialog-init** signal callback for initializing the `SettingsDialog`.
              
        This signal is ment to add pages to the `SettingsDialog`.

        :param dialog: The dialog to initialize.
        :type dialog: SettingsDialog
        """
        pass

