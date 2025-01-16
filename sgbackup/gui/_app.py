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

from gi.repository import Gtk,Gio,Gdk,GLib
from gi.repository.GObject import GObject,Signal,Property,SignalFlags,BindingFlags

import logging; logger=logging.getLogger(__name__)

import os
from datetime import datetime as DateTime
from pathlib import Path

from ..settings import settings
from ._settingsdialog import SettingsDialog
from ._gamedialog import GameDialog
from ..game import Game,GameManager,SAVEGAME_TYPE_ICONS
from ._steam import SteamLibrariesDialog,NewSteamAppsDialog

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
            
        factory_icon = Gtk.SignalListItemFactory.new()
        factory_icon.connect('setup',self._on_icon_column_setup)
        factory_icon.connect('bind',self._on_icon_column_bind)
        column_icon = Gtk.ColumnViewColumn.new("",factory_icon)
        
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
        
        factory_actions = Gtk.SignalListItemFactory.new()
        factory_actions.connect('setup',self._on_actions_column_setup)
        factory_actions.connect('bind',self._on_actions_column_bind)
        column_actions = Gtk.ColumnViewColumn.new("",factory_actions)
        
        selection = Gtk.SingleSelection.new(self._liststore)
        self.__columnview = Gtk.ColumnView.new(selection)
        self.columnview.append_column(column_icon)
        self.columnview.append_column(column_key)
        self.columnview.append_column(column_name)
        self.columnview.append_column(column_active)
        self.columnview.append_column(column_live)
        self.columnview.append_column(column_actions)
        self.columnview.set_single_click_activate(True)
        
        
        self.set_child(self.columnview)
        self.refresh()
        
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
            
    def _on_icon_column_setup(self,factory,item):
        item.set_child(Gtk.Image())
        
    def _on_icon_column_bind(self,factory,item):
        def transform_to_icon_name(_bidning,sgtype):
            icon_name = SAVEGAME_TYPE_ICONS[sgtype] if sgtype in SAVEGAME_TYPE_ICONS else None
            if icon_name:
                return icon_name
            return ""
        icon = item.get_child()
        game = item.get_item()
        game.bind_property('savegame_type',icon,'icon_name',BindingFlags.SYNC_CREATE,transform_to_icon_name)
        
        
        
        
    def _on_key_column_setup(self,factory,item):
        item.set_child(Gtk.Label())
        
    def _on_key_column_bind(self,factory,item):
        label = item.get_child()
        game = item.get_item()
        game.bind_property('key',label,'label',BindingFlags.SYNC_CREATE)
        
    def _on_name_column_setup(self,factory,item):
        item.set_child(Gtk.Label())
        
    def _on_name_column_bind(self,factory,item):
        label = item.get_child()
        game = item.get_item()
        game.bind_property('name',label,'label',BindingFlags.SYNC_CREATE)

    def _on_active_column_setup(self,factory,item):
        item.set_child(Gtk.Switch())
        
    def _on_active_column_bind(self,factory,item):
        switch = item.get_child()
        game = item.get_item()
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
        game = item.get_item()
        switch.set_active(game.is_live)
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
            
        game.is_live = switch.get_active()
        game.save()
        if not game.is_live:
            dialog = Gtk.MessageDialog()
            dialog.set_transient_for(self.get_root())
            dialog.props.buttons = Gtk.ButtonsType.YES_NO
            dialog.props.text = "Do you want to create a new savegame for <i>{game}</i>?".format(game=game.name)
            dialog.props.use_markup = True
            dialog.props.secondary_text = "The new savegame is added to the finsihed savegames for the game."
            dialog.props.secondary_use_markup = False
            dialog.connect('response',on_dialog_response)
            dialog.present()
    
    def _on_actions_column_setup(self,action,item):
        child = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,2)
        icon = Gtk.Image.new_from_icon_name('document-edit-symbolic')
        child.edit_button = Gtk.Button()
        child.edit_button.set_child(icon)
        child.append(child.edit_button)
        
        icon = Gtk.Image.new_from_icon_name('list-remove-symbolic')
        child.remove_button = Gtk.Button()
        child.remove_button.set_child(icon)
        child.append(child.remove_button)
        
        item.set_child(child)
        
    def _on_actions_column_bind(self,action,item):
        child = item.get_child()
        game = item.get_item()
        
        child.edit_button.connect('clicked',self._on_columnview_edit_button_clicked,item)
        child.remove_button.connect('clicked',self._on_columnview_remove_button_clicked,item)
    
    def _on_columnview_edit_button_clicked(self,button,item):
        def on_dialog_response(dialog,response):
            if response == Gtk.ResponseType.APPLY:
                self.refresh()
                
        game = item.get_item()
        dialog = GameDialog(self.get_root(),game)
        dialog.connect('response',on_dialog_response)
        dialog.present()
        
    def _on_columnview_remove_button_clicked(self,button,item):
        def on_dialog_response(dialog,response,game:Game):
            if response == Gtk.ResponseType.YES:
                if os.path.isfile(game.filename):
                    os.unlink(game.filename)
                for i in range(self._liststore.get_n_items()):
                    item = self._liststore.get_item(i)
                    if item.key == game.key:
                        self._liststore.remove_item(i)
                        return
                    
            dialog.hide()
            dialog.destroy()
            
        game = item.get_item()
        dialog = Gtk.MessageDialog(buttons=Gtk.ButtonsType.YES_NO,
                                   text="Do you really want to remove the game <span weight='bold'>{game}</span>?".format(
                                       game=game.name),
                                   use_markup=True,
                                   secondary_text="Removing games cannot be undone!!!")
        dialog.set_transient_for(self.get_root())
        dialog.connect('response',on_dialog_response,game)
        dialog.present()
        
# GameView class

class BackupViewData(GObject):
    """
    BackupViewData The data class for BackupView
    """
    
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
        """
        game The `Game` the data belong to

        :type: Game
        """
        return self.__game
    
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
        pass
    
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
    
    def _on_selection_changed(self,selection):
        pass

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
        self.__columnview.set_vexpand(True)
        
        self.gameview.columnview.connect('activate',self._on_gameview_columnview_activate)
        
        scrolled.set_child(self.__columnview)
        
        self.append(self._title_label)
        self.append(scrolled)
        
    @property
    def gameview(self)->GameView:
        """
        gameview The GameView this class is connected to.

        :type: GameView
        """
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
        
    def _on_gameview_columnview_activate(self,columnview,position):
        model = columnview.get_model().get_model()
        game = model.get_item(position)
        
        self._title_label.set_markup("<span size='large' weight='bold'>{}</span>".format(GLib.markup_escape_text(game.name)))
        
        

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
    
    def refresh(self):
        """
        refresh Refresh the views of this window.
        """
        self.gameview.refresh()
        #self.backupview.refresh()
        
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
        
        # add accels
        self.set_accels_for_action('app.quit',["<Primary>q"])
        
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
        pass
    
    def _on_action_settings(self,action,param):
        dialog = self.new_settings_dialog()
        dialog.present()
    
    def _on_action_quit(self,action,param):
        self.quit()
        
    def _on_dialog_response_refresh(self,dialog,response,check_response):
        if response == check_response:
            self.appwindow.refresh()
            
    def _on_action_new_game(self,action,param):
        dialog = GameDialog(self.appwindow)
        dialog.connect('response',
                       self._on_dialog_response_refresh,
                       Gtk.ResponseType.APPLY)
        dialog.present()
        
    def _on_action_steam_manage_libraries(self,action,param):
        dialog = SteamLibrariesDialog(self.appwindow)
        dialog.present()
        
    def _on_action_steam_new_apps(self,action,param):
        def on_dialog_response(dialog,response):
            self.appwindow.refresh()
            
        dialog = NewSteamAppsDialog(self.appwindow)
        dialog.connect('response',on_dialog_response)
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

