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

from gi.repository import Gtk,Gio,Gdk
from gi.repository.GObject import GObject,Signal,Property,SignalFlags

import logging; logger=logging.getLogger(__name__)

import os
from datetime import datetime as DateTime
from pathlib import Path

from ..settings import settings
from ._settingsdialog import SettingsDialog
from ._gamedialog import GameDialog
from ..game import Game,GameManager

__gtype_name__ = __name__

class GameView(Gtk.ScrolledWindow):
    """
    GameView The View for games.
        
    This is widget presents a clumnview for the installed games.
    """
    __gtype_name__ = "GameView"
    
    def __init__(self):
        """
        GameView
        """
        Gtk.ScrolledWindow.__init__(self)
        
        self.__liststore = Gio.ListStore.new(Game)
        for g in GameManager.get_global().games.values():
            pass
            self.__liststore.append(g)
            
        factory_key = Gtk.SignalListItemFactory.new()
        factory_key.connect('setup',self._on_key_column_setup)
        factory_key.connect('bind',self._on_key_column_bind)
        column_key = Gtk.ColumnViewColumn.new("Key",factory_key)
        
        factory_name = Gtk.SignalListItemFactory.new()
        factory_name.connect('setup',self._on_name_column_setup)
        factory_name.connect('bind',self._on_name_column_bind)
        column_name = Gtk.ColumnViewColumn.new("Name",factory_name) 
        column_name.set_expand(True)
        
        factory_active = Gtk.SignalListItemFactory.new()
        factory_active.connect('setup',self._on_active_column_setup)
        factory_active.connect('bind',self._on_active_column_bind)
        factory_active.connect('unbind',self._on_active_column_unbind)
        column_active = Gtk.ColumnViewColumn.new("Active",factory_active)
        
        factory_live = Gtk.SignalListItemFactory.new()
        factory_live.connect('setup',self._on_live_column_setup)
        factory_live.connect('bind',self._on_live_column_bind)
        factory_live.connect('unbind',self._on_live_column_unbind)
        column_live = Gtk.ColumnViewColumn.new("Live",factory_live)
        
        selection = Gtk.SingleSelection.new(self._liststore)
        self.__columnview = Gtk.ColumnView.new(selection)
        self.columnview.append_column(column_key)
        self.columnview.append_column(column_name)
        self.columnview.append_column(column_active)
        self.columnview.append_column(column_live)
        self.columnview.set_single_click_activate(True)
        
        self.set_child(self.columnview)
        
    @property
    def _liststore(self)->Gio.ListStore:
        """
        The `Gio.ListStore` that holds the list of installed games.

        
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
    
    def refresh(self):
        """
        refresh Refresh the view.
        
        This method reloads the installed Games.
        """
        self.__liststore.remove_all()
        for game in GameManager.get_global().games.values():
            self.__liststore.append(game)
            
    def _on_key_column_setup(self,factory,item):
        item.set_child(Gtk.Label())
        
    def _on_key_column_bind(self,factory,item):
        label = item.get_child()
        game = item.get_item()
        label.bind_property(game,'key','label',GObject.BindingFlags.DEFAULT)
        
    def _on_name_column_setup(self,factory,item):
        item.set_child(Gtk.Label())
        
    def _on_name_column_bind(self,factory,item):
        label = item.get_child()
        game = item.get_item()
        label.bind_proprety(game,'name','label',GObject.BindingFlags.DEFAULT)

    def _on_active_column_setup(self,factory,item):
        item.set_child(Gtk.Switch())
        
    def _on_active_column_bind(self,factory,item):
        switch = item.get_child()
        game = item.get_data()
        switch.set_active(game.is_active)
        item._signal_active_state_set = switch.connect('state-set',self._on_active_state_set,game)
        
    def _on_active_column_unbind(self,factory,item):
        if hasattr(item,'_signal_active_state_set'):
            item.get_child().disconnect(item._signal_active_state_set)
            del item._signal_active_state_set
        
    def _on_active_state_set(self,switch,state,game):
        game.is_active = state
        game.save()
        
    def _on_live_column_setup(self,factory,item):
        item.set_child(Gtk.Switch())
        
    def _on_live_column_bind(self,factory,item):
        switch = item.get_child()
        game = item.get_data()
        switch.set_active(game.is_active)
        item._signal_live_state_set = switch.connect('state-set',self._on_live_state_set,game)
        
    def _on_live_column_unbind(self,factory,item):
        if hasattr(item,'_signal_live_state_set'):
            item.get_child().disconnect(item._signal_live_state_set)
            del item._signal_live_state_set
        
    def _on_live_state_set(self,switch,state,game):
        def on_dialog_response(dialog,response):
            if response == Gtk.ResponseType.YES:
                pass
                #archiver.backup(game)
            dialog.hide()
            dialog.destroy()
            
        game.is_live = state
        game.save()
        if not state:
            dialog = Gtk.MessageDialog()
            dialog.set_transient_for(self.get_toplevel())
            dialog.props.buttons = Gtk.ButtonsType.YES_NO
            dialog.props.text = "Do you want to create a new savegame for <i>{game}</i>?".format(game=game.name)
            dialog.props.use_markup = True
            dialog.props.secondary_text = "The new savegame is added to the finsihed savegames for the game."
            dialog.props.secondary_use_markup = False
            dialog.connect('response',on_dialog_response)
            dialog.present()
    
    @property
    def current_game(self)->Game|None:
        """
        current_game Get the currently selected `Game`
        
        If no `Game` is selected this property resolves to `Null`

        :type: Game|None
        """
        selection = self._columnview.get_model()
        pos = selection.get_selected()
        if pos == Gtk.INVALID_LIST_POSITION:
            return None
        return selection.get_model().get_item(pos)
    
# GameView class

class BackupViewData(GObject):
    def __init__(self,_game:Game,filename:str):
        GObject.GObject.__init__(self)
        self.__game = _game
        self.__filename = filename
        
        basename = os.path.basename(filename)
        self.__is_live = (os.path.basename(os.path.dirname(filename)) == 'live')
        parts = filename.split('.')
        self.__savegame_name = parts[0]
        self.__timestamp = DateTime.strptime(parts[1],"%Y%m%d-%H%M%S")
        
        self.__extension = '.' + parts[3:]
        
    @property
    def game(self)->Game:
        return self.__game
    
    @Property
    def savegame_name(self):
        return self.__savegame_name
    
    @Property(type=str)
    def filename(self)->str:
        return self.__filename
    
    @Property(type=bool,default=False)
    def is_live(self)->bool:
        pass
    
    @Property
    def extension(self):
        return self.__extension
    
    @Property
    def timestamp(self):
        return self.__timestamp
    
    def _on_selection_changed(self,selection):
        pass

class BackupView(Gtk.ScrolledWindow):
    __gtype_name__ = "BackupView"
    def __init__(self,gameview:GameView):
        Gtk.ScrolledWindow.__init__(self)
        self.__gameview = gameview
        
        self.__liststore = Gio.ListStore()
        selection = Gtk.SingleSelection.new(self.__liststore)
        
        live_factory = Gtk.SignalListItemFactory()
        live_factory.connect('setup',self._on_live_column_setup)
        live_factory.connect('bind',self._on_live_column_bind)
        live_column = Gtk.ColumnViewColumn.new("Live",live_factory)
        
        sgname_factory = Gtk.SignalListItemFactory()
        sgname_factory.connect('setup',self._on_savegamename_column_setup)
        sgname_factory.connect('bind',self._on_savegamename_column_bind)
        sgname_column = Gtk.ColumnViewColumn.new("Savegame name",sgname_factory)
        sgname_column.set_expand(True)
        
        timestamp_factory = Gtk.SignalListItemFactory()
        timestamp_factory.connect('setup',self._on_timestamp_column_setup)
        timestamp_factory.connect('bind',self._on_timestamp_column_bind)
        timestamp_column = Gtk.ColumnViewColumn.new("Timestamp",timestamp_factory)
        
        self.__columnview = Gtk.ColumnView.new(selection)
        self.__columnview.append_column(live_column)
        self.__columnview.append_column(sgname_column)
        self.__columnview.append_column(timestamp_column)
        
        self._on_gameview_selection_changed(selection)
        self.gameview.columnview.get_model().connect('selection-changed',self._on_gameview_selection_changed)
        
        self.set_child(self.__columnview)
        
    @property
    def gameview(self)->GameView:
        return self.__gameview

    def _on_live_column_setup(self,factory,item):
        checkbutton = Gtk.CheckButton()
        checkbutton.set_sensitive(False)
        
    def _on_live_column_bind(self,factory,item):
        checkbutton = item.get_child()
        data = item.get_item()
        checkbutton.set_active(data.is_live)
        
    
    def _on_savegamename_column_setup(self,factory,item):
        label = Gtk.Label()
        self.set_child(label)
        
    def _on_savegamename_column_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_text(data.savegame_name)
        
    def _on_timestamp_column_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_timestamp_column_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_text(data.timestamp.strftime("%d.%m.%Y %H:%M:%S"))
        
    def _on_size_column_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_size_column_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        file = Path(data.filename).resolve()

        if not file.is_file():
            label.set_text("0 B")
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
        label.set_text(display_size)
        
    def _on_gameview_selection_changed(self,model):
        game = model.get_selected_item()
        if game is None:
            return
        

class AppWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "AppWindow"
    def __init__(self,application=None,**kwargs):
        kwargs['title'] = "SGBackup"
        
        if (application is not None):
            kwargs['application']=application
            if (hasattr(application,'builder')):
                builder = application.builder
            else:
                builder = Gtk.Builder.new()
                
        Gtk.ApplicationWindow.__init__(self,**kwargs)
        self.set_default_size(800,600)
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
        
        vbox.append(self.__vpaned)
        
        statusbar = Gtk.Statusbar()
        statusbar.set_hexpand(True)
        statusbar.set_vexpand(False)
        statusbar.push(0,'Running ...')
        vbox.append(statusbar)
        
        self.set_child(vbox)
        
    @property
    def builder(self):
        return self.__builder

    @property
    def backupview(self):
        return self.__backupview
    
    @property
    def gameview(self):
        return self.__gameview
    
    def refresh(self):
        self.gameview.refresh()
        #self.backupview.refresh()
        
class Application(Gtk.Application):
    __gtype_name__ = "Application"
    
    def __init__(self,*args,**kwargs):
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
    def appwindow(self):
        return self.__appwindow
    
    def do_startup(self):
        self._logger.debug('do_startup()')
        if not self.__builder:
            self.__builder = Gtk.Builder.new()
        Gtk.Application.do_startup(self)
        
        pkg_path = Path(__file__).resolve()
        pkg_path = pkg_path.parent.parent
        icons_path = pkg_path / "icons"
        
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        #theme.add_resource_path("/org/sgbackup/sgbackup/icons")
        theme.add_search_path(str(icons_path))
        
        action_about = Gio.SimpleAction.new('about',None)
        action_about.connect('activate',self.on_action_about)
        self.add_action(action_about)
        
        action_new_game = Gio.SimpleAction.new('new-game',None)
        action_new_game.connect('activate',self.on_action_new_game)
        self.add_action(action_new_game)
        
        action_quit = Gio.SimpleAction.new('quit',None)
        action_quit.connect('activate',self.on_action_quit)
        self.add_action(action_quit)
                
        action_settings = Gio.SimpleAction.new('settings',None)
        action_settings.connect('activate',self.on_action_settings)
        self.add_action(action_settings)
        
        # add accels
        self.set_accels_for_action('app.quit',["<Primary>q"])
        
    @Property
    def builder(self):
        return self.__builder
    
    def do_activate(self):
        self._logger.debug('do_activate()')
        if not (self.__appwindow):
            self.__appwindow = AppWindow(application=self)
            
        
        self.appwindow.present()
        
    def on_action_about(self,action,param):
        pass
    
    def on_action_settings(self,action,param):
        dialog = self.new_settings_dialog()
        dialog.present()
    
    def on_action_quit(self,action,param):
        self.quit()
        
    def _on_dialog_response_refresh(self,dialog,response,check_response):
        if response == check_response:
            self.appwindow.refresh()
            
    def on_action_new_game(self,action,param):
        dialog = GameDialog(self.appwindow)
        dialog.connect('response',
                       self._on_dialog_response_refresh,
                       Gtk.ResponseType.APPLY)
        dialog.present()        
        
    def new_settings_dialog(self):
        dialog = SettingsDialog(self.appwindow)
        self.emit('settings-dialog-init',dialog)
        return dialog
        
    @Signal(name='settings-dialog-init',
            flags=SignalFlags.RUN_LAST,
            return_type=None,
            arg_types=(SettingsDialog,))
    def do_settings_dialog_init(self,dialog):
        pass

