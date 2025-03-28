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

from gi.repository import Gtk,Gio,GLib
from gi.repository.GObject import GObject,Property,Signal,BindingFlags

from ..i18n import gettext as _

import os
from ..steam import (
    Steam,
    SteamLibrary,
    SteamApp,
    IgnoreSteamApp,
    PLATFORM_LINUX,
    PLATFORM_MACOS,
    PLATFORM_WINDOWS
)

from ..game import (
    GameManager,
    Game,
    SteamGameData,
    SteamLinuxData,
    SteamMacOSData,
    SteamWindowsData,
    SavegameType,
)


from ._gamedialog import GameDialog,GameSearchDialog

class SteamLibrariesDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self)
        self.set_title("SGBackup: Steam Libraries")
        self.set_default_size(620,480)
        if parent is not None:
            self.set_transient_for(parent)
            
        self.__steam = Steam()
        
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,2)
        icon = Gtk.Image.new_from_icon_name('list-add-symbolic')
        self.__add_lib_button=Gtk.Button()
        self.__add_lib_button.set_child(icon)
        self.__add_lib_button.connect('clicked',self._on_add_library_button_clicked)
        hbox.append(self.__add_lib_button)
        
        self.__lib_editable = Gtk.EditableLabel()
        self.__lib_editable.set_hexpand(True)
        self.__lib_editable.connect('changed',self._on_add_library_label_changed)
        self._on_add_library_label_changed(self.__lib_editable)
        hbox.append(self.__lib_editable)
        
        icon = Gtk.Image.new_from_icon_name('document-open-symbolic')
        self.__lib_chooser_button = Gtk.Button()
        self.__lib_chooser_button.set_child(icon)
        self.__lib_chooser_button.connect('clicked',self._on_choose_library_button_clicked)
        hbox.append(self.__lib_chooser_button)
        
        self.get_content_area().append(hbox)
        
        frame = Gtk.Frame.new(_("Steam libraries"))
        scrolled = Gtk.ScrolledWindow()
        
        self.__listmodel = Gio.ListStore.new(SteamLibrary)
        for lib in self.__steam.libraries:
            self.__listmodel.append(lib)
            
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_library_setup)
        factory.connect('bind',self._on_library_bind)
        
        selection = Gtk.SingleSelection.new(self.__listmodel)
        self.__listview = Gtk.ListView.new(selection,factory)
        
        scrolled.set_child(self.__listview)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        frame.set_child(scrolled)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        self.get_content_area().append(frame)
        
        self.add_button(_("Apply"),Gtk.ResponseType.APPLY)
        self.add_button(_("Cancel"),Gtk.ResponseType.CANCEL)
        
    def _on_add_library_button_clicked(self,button):
        try:
            steamlib = SteamLibrary(self.__lib_editable.get_text())
            for i in range(self.__listmodel.get_n_items()):
                item = self.__listmodel.get_item(i)
                if steamlib.directory == item.directory:
                    self.__lib_editable.set_text("")
                    return
                
            self.__listmodel.append(steamlib)
            self.__lib_editable.set_text("")
        except:
            pass
    
    def _on_choose_library_button_clicked(self,button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("SGBackup: Select Steam library path"))
        dialog.set_modal(True)
        if (self.__lib_editable.get_text() and os.path.isdir(self.__lib_editable.get_text())):
            dialog.set_initial_folder(Gio.File.new_for_path(self.__lib_editable.get_text()))
            
        dialog.select_folder(self,None,self._on_choose_library_select_folder)
        
    def _on_choose_library_select_folder(self,dialog,result,*args):
        try:
            file = dialog.select_folder_finish(result)
        except GLib.Error as ex:
            return
        
        if file is None:
            return
        
        self.__lib_editable.set_text(file.get_path())
            
    
    def _on_add_library_label_changed(self,label):
        if label.get_text() and os.path.isdir(label.get_text()):
            self.__add_lib_button.set_sensitive(True)
        else:
            self.__add_lib_button.set_sensitive(False)
            
    def _on_list_chooser_button_clicked(self,button,label):
        dialog = Gtk.FileDialog.new()
        dialog.set_initial_folder(Gio.File.new_for_path(label.get_text()))
        dialog.set_modal(True)
        dialog.set_title(_("SGBackup: Change Steam library path"))
        dialog.select_folder(self,None,self._on_list_chooser_dialog_select_folder,label)
        
    def _on_list_chooser_dialog_select_folder(self,dialog,result,label,*data):
        try:
            file = dialog.select_folder_finish(result)
        except GLib.Error as ex:
            return
        
        if file is None or not file.get_path():
            return
        
        label.set_text(file.get_path())
        
    
    def _on_list_remove_button_clicked(self,button,label):
        for i in range(self.__listmodel.get_n_items()):
            item = self.__listmodel.get_item(i)
            if label.get_text() == item.directory:
                self.__listmodel.remove(i)
                return
    
    def _on_library_setup(self,factory,item):
        child = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,2)
        child.label = Gtk.EditableLabel()
        child.label.set_hexpand(True)
        child.append(child.label)
        
        icon = Gtk.Image.new_from_icon_name('document-open-symbolic')
        child.chooser_button = Gtk.Button()
        child.chooser_button.set_child(icon)
        child.append(child.chooser_button)
        
        icon = Gtk.Image.new_from_icon_name('list-remove-symbolic')
        child.remove_button = Gtk.Button()
        child.remove_button.set_child(icon)
        child.append(child.remove_button)
        
        item.set_child(child)
        
    
    def _on_library_bind(self,factory,item):
        child = item.get_child()
        lib = item.get_item()
        child.label.set_text(lib.directory)
        child.label.bind_property('text',lib,'directory',BindingFlags.DEFAULT)
        if hasattr(child.chooser_button,'_signal_clicked_connector'):
            child.chooser_button.disconnect(child.chooser_button._signal_clicked_connector)
        child.chooser_button._signal_clicked_connector = child.chooser_button.connect('clicked',
                                                                                      self._on_list_chooser_button_clicked,
                                                                                      child.label)
        
        if hasattr(child.remove_button,'_signal_clicked_connector'):
            child.remove_button.disconnect(child.remove_button._signal_clicked_connector)
        child.remove_button._signal_clicked_connector = child.remove_button.connect('clicked',
                                                                                    self._on_list_remove_button_clicked,
                                                                                    child.label)
        
    def do_response(self,response):
        if response == Gtk.ResponseType.APPLY:
            steamlibs = []
            for i in range(self.__listmodel.get_n_items()):
                item = self.__listmodel.get_item(i)
                if os.path.isdir(item.directory):
                    steamlibs.append(item)
            self.__steam.libraries = steamlibs                
        
        self.hide()
        self.destroy()
        

class NewSteamAppSorter(Gtk.Sorter):
    def do_compare(self,item1:SteamApp,item2:SteamApp):
        s1=item1.name.lower()
        s2=item2.name.lower()
        
        if s1 < s2:
            return Gtk.Ordering.SMALLER
        elif s1 > s2:
            return Gtk.Ordering.LARGER
        else:
            return Gtk.Ordering.EQUAL


class SteamGameLookupDialog(GameSearchDialog):
    def __init__(self,parent,steam_app:SteamApp):
        GameSearchDialog.__init__(self,parent,steam_app.name,_("Search Steam Apps"))
        self.__steam_app = steam_app
    @Property
    def steam_app(self)->SteamApp:
        return self.__steam_app
    
    def do_prepare_game(self, game):
        game = super().do_prepare_game(game)
        if game.steam:
            if not game.steam.appid != self.steam_app.appid and game.steam_appid >= 0:
                raise ValueError("Steam appid error")
            
            if PLATFORM_WINDOWS:
                if not game.steam.windows:
                    game.steam.windows = SteamWindowsData("","",installdir=self.steam_app.installdir)
                else:
                    game.steam.windows.installdir=self.steam_app.installdir
            if PLATFORM_LINUX:
                if not game.steam.linux:
                    game.steam.linux = SteamLinuxData("","",installdir=self.steam_app.installdir)
                else:
                    game.steam.linux.installdir=self.steam_app.installdir
                    
            if PLATFORM_MACOS:
                if not game.steam.macos:
                    game.steam.macos = SteamWindowsData("","",installdir=self.steam_app.installdir)
                else:
                    game.steam.macos.installdir=self.steam_app.installdir
        else:
            if PLATFORM_WINDOWS:
                windows = SteamWindowsData("","",installdir=self.steam_app.installdir)
            else:
                windows = None
                
            if PLATFORM_LINUX:
                linux = SteamLinuxData("","",installdir=self.steam_app.installdir)
            else:
                linux = None
                
            if PLATFORM_MACOS:
                macos = SteamMacOSData("","",installdir=self.steam_app.installdir)
            else:
                macos = None
                
            game.steam = SteamGameData(appid=self.steam_app.appid,
                                       windows=windows,
                                       linux=linux,
                                       macos=macos)
            
            return game
        

class NewSteamAppsDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self)
        if parent:
            self.set_transient_for(parent)
            
        self.set_title(_('SGBackup: New Steam apps'))
        self.set_default_size(800,600)
        self.__steam = Steam()
        
        self.__listmodel = Gio.ListStore.new(SteamApp)
        for app in self.__steam.find_new_steamapps():
            self.__listmodel.append(app)
        
        sortmodel = Gtk.SortListModel.new(self.__listmodel,NewSteamAppSorter())
        selection = Gtk.SingleSelection.new(sortmodel)
        selection.set_can_unselect(True)
        selection.set_autoselect(False)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_listitem_setup)
        factory.connect('bind',self._on_listitem_bind)
        
        self.__listview = Gtk.ListView.new(selection,factory)
        self.__listview.set_vexpand(True)
        self.__listview.set_show_separators(True)
        self.__listview.set_single_click_activate(True)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.__listview)
        scrolled.set_vexpand(True)
        
        self.get_content_area().append(scrolled)
        
        self.__gamedialog = None
        
        self.add_button("OK",Gtk.ResponseType.OK)
        
    def _on_listitem_setup(self,factory,item):
        grid = Gtk.Grid()
        grid.set_hexpand(True)
        grid.set_column_spacing(5)
        
        #label = Gtk.Label.new("Name:")
        #label.set_xalign(0.0)
        grid.name_label = Gtk.Label()
        grid.name_label.set_hexpand(True)
        grid.name_label.set_xalign(0.0)
        #grid.attach(label,0,0,1,1)
        grid.attach(grid.name_label,1,0,1,1)
        
        label = Gtk.Label.new("AppID:")
        label.set_xalign(0.0)
        grid.appid_label = Gtk.Label()
        grid.appid_label.set_hexpand(True)
        grid.appid_label.set_xalign(0.0)
        grid.attach(label,0,1,1,1)
        grid.attach(grid.appid_label,1,1,1,1)
        
        label = Gtk.Label.new("Installdir:")
        label.set_xalign(0.0)
        grid.installdir_label = Gtk.Label()
        grid.installdir_label.set_hexpand(True)
        grid.installdir_label.set_xalign(0.0)
        grid.attach(label,0,2,1,1)
        grid.attach(grid.installdir_label,1,2,1,1)
        
        # Buttons    
        button_grid = Gtk.Grid()
        button_grid.set_column_spacing(2)
        button_grid.set_row_spacing(2)
        
        icon = Gtk.Image.new_from_icon_name('list-add-symbolic')
        icon.set_pixel_size(16)
        grid.add_app_button = Gtk.Button()
        grid.add_app_button.set_child(icon)
        grid.add_app_button.set_tooltip_markup(_('Add SteamApp as new Game.'))
        button_grid.attach(grid.add_app_button,0,0,1,1)
        
        icon = Gtk.Image.new_from_icon_name('edit-delete-symbolic')
        icon.set_pixel_size(16)
        grid.ignore_app_button = Gtk.Button()
        grid.ignore_app_button.set_child(icon)
        grid.ignore_app_button.set_tooltip_text(_('Add SteamApp to ignore list.'))
        button_grid.attach(grid.ignore_app_button,1,0,1,1)
    
        icon = Gtk.Image.new_from_icon_name('edit-find-symbolic')
        icon.set_pixel_size(16)
        grid.lookup_button = Gtk.Button()
        grid.lookup_button.set_child(icon)
        grid.lookup_button.set_tooltip_text(_("Lookup SteamApp for already registered game."))
        button_grid.attach(grid.lookup_button,0,1,1,1)
        
        icon = Gtk.Image.new_from_icon_name('folder-download-symbolic')
        icon.set_pixel_size(16)
        grid.search_online_button = Gtk.Button()
        grid.search_online_button.set_child(icon)
        grid.search_online_button.set_tooltip_text(_("Lookup SteamApp online."))
        button_grid.attach(grid.search_online_button,1,1,1,1)
        
        grid.attach(button_grid,3,0,1,3)
        
        item.set_child(grid)
        
    def _on_listitem_bind(self,factory,item):
        child = item.get_child()
        data = item.get_item()
        
        child.name_label.set_markup("<span weight='bold' size='large'>{}</span>".format(GLib.markup_escape_text(data.name)))
        child.appid_label.set_text(str(data.appid))
        child.installdir_label.set_text(data.installdir)
        
        # Check if we are already connected.
        # if we dont check we might have more than one dialog open
        # due to Gtk4 reusing the widgets.
        # When selecting a row in the columnview this method is called so we 
        # need to ensure that the last binding is used to work as expected.
        if hasattr(child.add_app_button,'_signal_clicked_connector'):
            child.add_app_button.disconnect(child.add_app_button._signal_clicked_connector)
        child.add_app_button._signal_clicked_connector = child.add_app_button.connect('clicked',self._on_add_steamapp_button_clicked,data)
        
        if hasattr(child.ignore_app_button,'_signal_clicked_connector'):
            child.ignore_app_button.disconnect(child.ignore_app_button._signal_clicked_connector)
        child.ignore_app_button._signal_clicked_connector = child.ignore_app_button.connect('clicked',self._on_ignore_steamapp_button_clicked,data)
        
        if hasattr(child.lookup_button,'_signal_clicked_connector'):
            child.lookup_button.disconnect(child.lookup_button._signal_clicked_connector)
        child.lookup_button._signal_clicked_connector = child.lookup_button.connect('clicked',self._on_lookup_steamapp_button_clicked,data)
        
        if hasattr(child.search_online_button,'_signal_clicked_connector'):
            child.search_online_button.disconnect(child.search_online_button._signal_clicked_connector)
        #child.search_button._signal_clicked_connector = child.search_online_button.connect('clicked',self._on_lookup_steamapp_button_clicked,data)
        child.search_online_button.set_sensitive(False)
        
    def _on_add_steamapp_button_clicked(self,button,data:SteamApp,*args):
        def on_dialog_response(dialog,response):
            if (response == Gtk.ResponseType.APPLY):
                for i in reversed(range(self.__listmodel.get_n_items())):
                    item = self.__listmodel.get_item(i)
                    if item.appid == data.appid:
                        self.__listmodel.remove(i)
                    
        game = Game("",data.name,"")
        game.steam = SteamGameData(appid=data.appid)
        if PLATFORM_WINDOWS:
            game.steam.windows = SteamWindowsData("","",installdir=data.installdir)
            game.savegame_type = SavegameType.STEAM_WINDOWS
        elif PLATFORM_LINUX:
            game.steam.linux = SteamLinuxData("","",installdir=data.installdir)
            game.savegame_type = SavegameType.STEAM_LINUX
        elif PLATFORM_MACOS:
            game.steam.macos = SteamMacOSData("","",installdir=data.installdir)
            game.savegame_type = SavegameType.STEAM_MACOS
        
        gamedialog = GameDialog(self,game)
        gamedialog.set_title(_("SGBackup: Add Steam Game"))
        gamedialog.set_modal(False)
        gamedialog.connect_after('response',on_dialog_response)
        gamedialog.present()
    
    def _on_ignore_steamapp_button_clicked(self,button,data:SteamApp,*args):
        def on_dialog_response(dialog,response,data:SteamApp):
            dialog.hide()
            dialog.destroy()
            if response == Gtk.ResponseType.YES:
                ignore = IgnoreSteamApp(data.appid,data.name,dialog.reason_entry.get_text())
                self.__steam.add_ignore_app(ignore)
                for i in reversed(range(self.__listmodel.get_n_items())):
                    item = self.__listmodel.get_item(i)
                    if item.appid == data.appid:
                        self.__listmodel.remove(i)
        
        dialog = Gtk.MessageDialog(buttons=Gtk.ButtonsType.YES_NO)
        dialog.set_transient_for(self)
        dialog.set_modal(False)
        dialog.props.text = _("Do you want to put <span weight=\"bold\">\"{steamapp}\"</span> on the ignore list?").format(
            steamapp=GLib.markup_escape_text(data.name))
        dialog.props.use_markup = True
        
        dialog.props.secondary_text = _("Please enter the reason for ignoring this app.")
        dialog.reason_entry = Gtk.Entry()
        dialog.reason_entry.set_hexpand(True)
        dialog.get_content_area().append(dialog.reason_entry)
        
        dialog.connect('response',on_dialog_response,data)
        dialog.present()
        
    def _on_lookup_steamapp_button_clicked(self,dialog,data:SteamApp):
        dialog = SteamGameLookupDialog(parent=self,steam_app=data)
        dialog.present()
    
    def refresh(self):
        self.__listmodel.remove_all()
        for app in self.__steam.find_new_steamapps():
            self.__listmodel.append(app)
            
    def do_response(self,response):
        self.hide()
        self.destroy()

class SteamNoNewAppsDialog(Gtk.MessageDialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.MessageDialog.__init__(self,buttons=Gtk.ButtonsType.OK)
        if parent:
            self.set_transient_for(parent)

        self.props.text = _("There were no new Steam-Apps found!")
        self.props.use_markup = False

    def do_response(self,response):
        self.hide()
        self.destroy()
        
        
### SteamIgnoreApps ###########################################################

class SteamNoIgnoredAppsDialog(Gtk.MessageDialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.MessageDialog.__init__(self,buttons=Gtk.ButtonsType.OK)
        if parent:
            self.set_transient_for(parent)
            
        self.props.text = _("There are no Steam-Apps that are ignored!")
        self.props.use_markup = False
        
    def do_response(self,response):
        self.hide()
        self.destroy()


class SteamIgnoreAppsSorter(Gtk.Sorter):
    def do_compare(self,item1:IgnoreSteamApp,item2:IgnoreSteamApp):
        s1 = item1.name.lower()
        s2 = item2.name.lower()
        
        if s1 > s2:
            return Gtk.Ordering.LARGER
        elif s1 < s2:
            return Gtk.Ordering.SMALLER
        else:
            return Gtk.Ordering.EQUAL

class SteamIgnoreAppsDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self)
        self.set_default_size(640,480)
        self.set_title(_("SGBackup: manage ignored SteamApps"))
        if parent:
            self.set_transient_for(parent)
        self.set_modal(False)

        steam = Steam()
        
        self.__liststore = Gio.ListStore.new(IgnoreSteamApp)
        for sia in steam.ignore_apps.values():
            self.__liststore.append(sia)
            
        self.__sortmodel = Gtk.SortListModel(model=self.__liststore,sorter=SteamIgnoreAppsSorter())
        self.__selection = Gtk.SingleSelection(model=self.__sortmodel,
                                               can_unselect=True,
                                               autoselect=True)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_listview_setup)
        factory.connect('bind',self._on_listview_bind)
        
        self.__listview = Gtk.ListView(model=self.__selection,
                                       factory=factory,
                                       single_click_activate=True,
                                       enable_rubberband=True)
        self.__listview.set_vexpand(True)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.__listview)
        scrolled.set_vexpand(True)
        self.get_content_area().append(scrolled)
        
        self.add_button(_("Close"),Gtk.ResponseType.OK)
        
    def _on_listview_setup(self,factory,item):
        child = Gtk.Grid(column_spacing=4,row_spacing=5)
        child.name_label = Gtk.Label()
        child.name_label.set_xalign(0.0)
        child.name_label.set_hexpand(True)
        child.attach(child.name_label,1,0,2,1)
        
        label = Gtk.Label.new(_("Reason:"))
        label.set_xalign(0.0)
        child.reason_label = Gtk.Label()
        child.reason_label.set_xalign(0.0)
        child.reason_label.set_hexpand(True)
        child.attach(label,0,1,1,1)
        child.attach(child.reason_label,1,1,1,1)
        
        action_grid = Gtk.Grid()
        
        icon = Gtk.Image.new_from_icon_name("document-new-symbolic")
        icon.set_pixel_size(16)
        child.new_game_button = Gtk.Button()
        child.new_game_button.set_child(icon)
        child.new_game_button.set_tooltip_text("Add ignored SteamApp as a new game.")
        action_grid.attach(child.new_game_button,0,0,1,1)
        
        icon = Gtk.Image.new_from_icon_name("list-remove-symbolic")
        icon.set_pixel_size(16)
        child.remove_button = Gtk.Button()
        child.remove_button.set_child(icon)
        child.remove_button.set_tooltip_text("Remove ignored SteamApp from the list.")
        action_grid.attach(child.remove_button,0,1,1,1)
        
        child.attach(action_grid,2,0,1,2)
        
        item.set_child(child)
    
    def _on_listview_bind(self,factory,item):
        child = item.get_child()
        data = item.get_item()
        
        child.name_label.set_markup("<span size='x-large' weight='bold'>{}</span>".format(GLib.markup_escape_text(data.name)))
        child.reason_label.set_text(data.reason)
        
        if hasattr(child.new_game_button,'_sginal_clicked_connector'):
            child.new_game_button.disconnect(child.new_game_button._signal_clicked_connector)
        child.new_game_button._signal_clicked_connector = child.new_game_button.connect('clicked',self._on_new_game_button_clicked,data)
        
        if hasattr(child.remove_button,'_signal_clicked_connector'):
            child.remove_button.disconnect(child.remove_button._signal_clicked_connector)
        child.remove_button._signal_clicked_connector = child.remove_button.connect('clicked',self._on_remove_button_clicked,data)
    
    def __remove_item(self,item:IgnoreSteamApp):
        for i in range(self.__liststore.get_n_items()):
            ignoreapp = self.__liststore.get_item(i)
            if item.appid == ignoreapp.appid:
                self.__liststore.remove(i)
                break
        
    def _on_remove_button_clicked(self,button,item:IgnoreSteamApp):
        self.__remove_item(item)
        steam = Steam()
        steam.remove_ignore_app(item)
    
    def _on_new_game_button_clicked(self,button,item:IgnoreSteamApp):
        game = None
        steam = Steam()
        steam.remove_ignore_app(item)
        steam = Steam()
        steamapps = steam.find_new_steamapps()
        for steamapp in steamapps:
            if steamapp.appid == item.appid:
                game = Game("",steamapp.name,"")
                if PLATFORM_WINDOWS:
                    windows = SteamWindowsData("","",installdir=steamapp.installdir)
                    game.savegame_type = SavegameType.STEAM_WINDOWS
                else:
                    windows = None
                    
                if PLATFORM_LINUX:
                    linux = SteamLinuxData("","",installdir=steamapp.installdir)
                    game.savegame_type = SavegameType.STEAM_LINUX
                else:
                    linux = None
                    
                if PLATFORM_MACOS:
                    macos = SteamMacOSData("","",installdir=steamapp.installdir)
                    game.savegame_type = SavegameType.STEAM_MACOS
                else:
                    macos = None
                
                steamdata = SteamGameData(steamapp.appid,
                                          windows=windows,
                                          linux=linux,
                                          macos=macos)
                game.steam = steamdata
                break
            
        if game is None:
            gamemanager = GameManager.get_global()
            for g in gamemanager.games.values():
                if g.steam and g.steam.appid == item.appid:
                    game = g
                    break
        
        if game is None:
            game = Game("",item.name,"")
            if PLATFORM_WINDOWS:
                game.savegame_type = SavegameType.STEAM_WINDOWS
            elif PLATFORM_LINUX:
                game.savegame_type = SavegameType.STEAM_LINUX
            elif PLATFORM_MACOS:
                game.savegame_type = SavegameType.STEAM_MACOS
            game.steam = SteamGameData(steamapp.appid)
            
        dialog = GameDialog(self.get_transient_for(),game=game)
        dialog.present()

    def _on_game_dialog_response(self,dialog,response,item=IgnoreSteamApp):
        if response == Gtk.ResponseType.APPLY:
            self.__remove_item(item)
        else:
            steam = Steam()
            steam.add_ignore_app(item)
            
    def do_response(self,response):
        self.hide()
        self.destroy()
        