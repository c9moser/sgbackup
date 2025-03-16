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

from gi.repository import Gtk,GLib,Gio
from gi.repository.GObject import GObject,Property,Signal,SignalFlags

from ..i18n import gettext as _,gettext_noop as N_
from ..game import GameManager,Game,EpicGameData,EpicWindowsData
from ..epic import Epic,EpicGameInfo,EpicIgnoredApp
from ._gamedialog import GameSearchDialog
from ..utility import PLATFORM_WINDOWS

from ._gamedialog import GameDialog

class EpicNoNewAppsDialog(Gtk.MessageDialog):
    def __init__(self,parent:Gtk.Window|None):
        Gtk.MessageDialog.__init__(self,
                                   transient_for=parent,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=_("There were no new Epic-Games apps found!"),
                                   use_markup=False,
                                   modal=True)
        
    def do_response(self,response):
        self.hide()
        self.destroy()


class EpicNoIgnoredAppsDialog(Gtk.MessageDialog):
    def __init__(self,parent:Gtk.Window|None):
        Gtk.MessageDialog.__init__(self,
                                   transient_for=parent,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=_("There are no ignored Epic-Games apps!"),
                                   use_markup=False,
                                   modal=True)
        
    def do_response(self,response):
        self.hide()
        self.destroy()
        
### EpicLookupGamesDialog #####################################################

class EpicLookupGamesDialog(GameSearchDialog):
    def __init__(self,parent:Gtk.Window|None=None,info:EpicGameInfo|None=None):
        GameSearchDialog.__init__(self,parent,info.name if info else None)
        self.__gameinfo = info
        
    @Property
    def gameinfo(self)->EpicGameInfo|None:
        return self.__gameinfo
    
    @gameinfo.setter
    def gameinfo(self,info:EpicGameInfo|None):
        if info:
            self.search_name = info.name
        else:
            self.search_name = None
        self.__gameinfo = info
        
    def do_prepare_game(self,game:Game):
        game = super().do_prepare_game(game)
        if self.gameinfo:
            if game.epic:
                game.epic.catalog_item_id = self.gameinfo.catalog_item_id
            else:
                game.epic = EpicGameData(self.gameinfo.catalog_item_id)
            if PLATFORM_WINDOWS:
                if not game.epic.windows:
                    game.epic.windows = EpicWindowsData("","",installdir=self.gameinfo.installdir)
                else:
                    game.epic.windows.installdir = self.gameinfo.installdir
        else:
            if not game.epic:
                game.epic = EpicGameData()
            if PLATFORM_WINDOWS and not game.epic.windows:
                game.epic.windows = EpicWindowsData("","")
                
        return game

### EpicNewGamesDialog ########################################################

class EpicNewAppsDialogSorter(Gtk.Sorter):
    def do_compare(self,item1:EpicGameInfo,item2:EpicGameInfo):
        name1 = item1.name.lower()
        name2 = item2.name.lower()
        
        if name1 > name2:
            return Gtk.Ordering.LARGER
        elif name1 < name2:
            return Gtk.Ordering.SMALLER
        return Gtk.Ordering.EQUAL

class EpicNewAppsDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self,
                            transient_for=parent,
                            title=_("SGBackup: Manage new Epic-Games apps"),
                            modal=False)
        
        self.set_default_size(800,600)
        scrolled = Gtk.ScrolledWindow()
        
        epic = Epic()
        self.__liststore = Gio.ListStore.new(EpicGameInfo)
        for info in epic.find_new_apps():
            self.__liststore.append(info)
            
        sort_model = Gtk.SortListModel(model=self.__liststore,
                                       sorter=EpicNewAppsDialogSorter())
        selection = Gtk.SingleSelection(model=sort_model,
                                        autoselect=False,
                                        can_unselect=True)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_listview_setup)
        factory.connect('bind',self._on_listview_bind)
        
        self.__listview = Gtk.ListView(model=selection,factory=factory,hexpand=True,vexpand=True)
        scrolled.set_child(self.__listview)
        self.get_content_area().append(scrolled)
        self.__close_button = self.add_button(_("Close"),Gtk.ResponseType.OK)
        

    def _on_listview_setup(self,factory,item):
        child = Gtk.Grid(column_spacing=4,row_spacing=2)
        
        child.name_label = Gtk.Label(xalign=0.0,hexpand=True)
        child.attach(child.name_label,1,0,1,1)
        
        label = Gtk.Label(label=_("CatalogItemId:"),
                          use_markup=False,
                          xalign=0.0)
        child.catalogitemid_label = Gtk.Label(xalign=0.0,
                                              use_markup=False,
                                              hexpand=True)
        child.attach(label,0,1,1,1)
        child.attach(child.catalogitemid_label,1,1,1,1)
        
        label = Gtk.Label(label=_("Installation Directory:"),
                          use_markup=False,
                          xalign=0.0)
        child.installdir_label = Gtk.Label(xalign=0.0,
                                           use_markup=False,
                                           hexpand=True)
        child.attach(label,0,2,1,1)
        child.attach(child.installdir_label,1,2,1,1)
        
        actiongrid = Gtk.Grid(row_spacing=2,column_spacing=2)
        
        icon = Gtk.Image.new_from_icon_name('list-add-symbolic')
        icon.set_pixel_size(16)
        child.new_button = Gtk.Button()
        child.new_button.set_child(icon)
        child.new_button.set_tooltip_text(_("Add Epic-Games-app as a new game."))
        actiongrid.attach(child.new_button,0,0,1,1)
        
        icon = Gtk.Image.new_from_icon_name('edit-delete-symbolic')
        icon.set_pixel_size(16)
        child.ignore_button = Gtk.Button()
        child.ignore_button.set_child(icon)
        child.ignore_button.set_tooltip_text(_("Add Epic-Games-app to the ignore list."))
        actiongrid.attach(child.ignore_button,1,0,1,1)
        
        icon = Gtk.Image.new_from_icon_name('edit-find-symbolic')
        icon.set_pixel_size(16)
        child.lookup_button = Gtk.Button()
        child.lookup_button.set_child(icon)
        child.lookup_button.set_tooltip_text(_("Lookup Epic-Games-app for already registered game."))
        actiongrid.attach(child.lookup_button,0,1,1,1)
        
        icon = Gtk.Image.new_from_icon_name('folder-download-symbolic')
        icon.set_pixel_size(16)
        child.online_button = Gtk.Button()
        child.online_button.set_child(icon)
        child.online_button.set_tooltip_text(_("Lookup Epic-Games-app online."))
        actiongrid.attach(child.online_button,1,1,1,1)
        
        child.attach(actiongrid,2,0,1,3)
        item.set_child(child)
        
    
    def _on_listview_bind(self,factory,item):
        child = item.get_child()
        data = item.get_item()
        
        child.name_label.set_markup("<span size='large' weight='bold'>{}</span>".format(
            GLib.markup_escape_text(data.name)))
        child.catalogitemid_label.set_text(data.catalog_item_id)
        child.installdir_label.set_text(data.installdir)
        
        if hasattr(child.new_button,'_signal_clicked_connector'):
            child.new_button.disconnect(child.new_button._signal_clicked_connector)
        child.new_button._signal_clicked_connector = child.new_button.connect('clicked',
                                                                              self._on_listview_new_button_clicked,
                                                                              data)
        
        if hasattr(child.ignore_button,'_signal_clicked_connector'):
            child.ignore_button.disconnect(child.ignore_button._signal_clicked_connector)
        child.ignore_button._signal_clicked_connector = child.ignore_button.connect('clicked',
                                                                                    self._on_listview_ignore_button_clicked,
                                                                                    data)
        
        if hasattr(child.lookup_button,'_signal_clicked_connector'):
            child.lookup_button.disconnect(child.lookup_button._signal_clicked_connector)
        child.lookup_button._signal_clicked_connector = child.lookup_button.connect('clicked',
                                                                                    self._on_listview_lookup_button_clicked,
                                                                                    data)
        
        if hasattr(child.online_button,'_signal_clicked_connector'):
            child.online_button.disconnect(child.online_button._signal_clicked_connector)
        child.online_button._signal_clicked_connector = child.online_button.connect('clicked',
                                                                                    self._on_listview_online_button_clicked,
                                                                                    data)
        child.online_button.set_sensitive(False)
        
    def _on_game_dialog_response(self,dialog,response,info:EpicGameInfo):
        if response == Gtk.ResponseType.APPLY:
            for i in range(self.__liststore.get_n_items()):
                item = self.__liststore.get_item(i)
                if item.catalog_item_id == info.catalog_item_id:
                    self.__liststore.remove(i)
                    break
            
            
    def _on_listview_new_button_clicked(self,button:Gtk.Button,info:EpicGameInfo):
        game = Game("",info.name,"")
        if PLATFORM_WINDOWS:
            windows = EpicWindowsData("","",installdir=info.installdir)
        else:
            windows = None
            
        game.epic = EpicGameData(catalog_item_id=info.catalog_item_id,
                                 windows=windows)
        
        dialog = GameDialog(parent=self,game=game)
        dialog.connect_after('response',self._on_dialog_reponse,info)
        dialog.present()
        
    
    def _on_ignore_dialog_response(self,dialog,response,info:EpicGameInfo):
        if response == Gtk.ResponseType.YES:
            epic = Epic()
            epic.add_ignored_app(EpicIgnoredApp(info.catalog_item_id,
                                                info.name,
                                                dialog.reason_entry.get_text()))
            for i in range(self.__liststore.get_n_items()):
                item = self.__liststore.get_item(i)
                if item.catalog_item_id == info.catalog_item_id:
                    self.__liststore.remove(i)
                    break
                
        dialog.hide()
        dialog.destroy()
    
    def _on_listview_ignore_button_clicked(self,button:Gtk.Button,info:EpicGameInfo):
        dialog = Gtk.MessageDialog(transient_for=self,
                                   text=_("Do you really won to add the game <i>{game}</i> to the ignore list?").format(
                                       game=GLib.markup_escape_text(info.name)),
                                    use_markup=True,
                                    secondary_text=_("Please enter a reason below."),
                                    secondary_use_markup=True,
                                    buttons=Gtk.ButtonsType.YES_NO,
                                    modal=False)
        dialog.reason_entry = Gtk.Entry()
        dialog.reason_entry.set_hexpand(True)
        dialog.get_content_area().append(dialog.reason_entry)
        dialog.connect('response',self._on_ignore_dialog_response,info)
        dialog.present()
        
    def _on_listview_lookup_button_clicked(self,button:Gtk.Button,info:EpicGameInfo):
        dialog = EpicLookupGamesDialog(parent=self,info=info)
        dialog.present()
    
    def _on_listview_online_button_clicked(self,button:Gtk.Button,info:EpicGameInfo):
        pass
    
    def do_response(self,response):
        self.hide()
        self.destroy()

    def refresh(self):
        epic = Epic()
        self.__liststore.remove_all()
        
        for gameinfo in epic.find_new_apps():
            self.__liststore.append(gameinfo)

#### EpicIgnoreAppsDialog ##########################################################

class EpicIgnoredAppsDialogSorter(Gtk.Sorter):
    def do_compare(self,item1:EpicIgnoredApp,item2:EpicIgnoredApp):
        name1=item1.name.lower()
        name2=item2.name.lower()
        
        if name1 < name2:
            return Gtk.Ordering.SMALLER
        elif name1 > name2:
            return Gtk.Ordering.LARGER
        
        return Gtk.Ordering.EQUAL
    

class EpicIgnoredAppsDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self,transient_for=parent)
        self.set_default_size(640,480)
        
        epic = Epic()
        self.__liststore = Gio.ListStore.new(EpicIgnoredApp)
        for ignored in epic.ignored_apps.values():
            self.__liststore.append(ignored)
    
        sort_model = Gtk.SortListModel(model=self.__liststore,sorter=EpicIgnoredAppsDialogSorter())
        selection = Gtk.SingleSelection(model=sort_model)
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_listview_item_setup)
        factory.connect('bind',self._on_listview_item_bind)
        
        self.__listview = Gtk.ListView(model=selection,
                                       factory=factory,
                                       hexpand=True,
                                       vexpand=True)
        
        scrolled = Gtk.ScrolledWindow(hexpand=True,
                                      vexpand=True)
        scrolled.set_child(self.__listview)
        self.get_content_area().append(scrolled)
        
        self.add_button("Close",Gtk.ResponseType.OK)
        
    def _on_listview_item_setup(self,factory,item):
        child = Gtk.Grid(hexpand=True,column_spacing=4,row_spacing=2)
        
        child.name_label = Gtk.Label(use_markup=True,xalign=0.0,hexpand=True)
        child.attach(child.name_label,1,0,1,1)
        
        label = Gtk.Label(label=_("CatalogItemId:"),use_markup=False,xalign=0.0,hexpand=False)
        child.catalogitemid_label = Gtk.Label(use_markup=False,xalign=0.0,hexpand=True)
        child.attach(label,0,1,1,1)
        child.attach(child.catalogitemid_label,1,1,1,1)
        
        label = Gtk.Label(label=_("Reason:"),use_markup=False,xalign=0.0,hexpand=False)
        child.reason_label = Gtk.Label(use_markup=True,xalign=0.0,hexpand=True)
        child.attach(label,0,2,1,1)
        child.attach(child.reason_label,1,2,1,1)
        
        action_grid = Gtk.Grid(column_spacing=2,row_spacing=2)
        
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
        
        child.attach(action_grid,2,0,1,3)
        
        item.set_child(child)
    
    def _on_listview_item_bind(self,factory,item):
        child = item.get_child()
        data = item.get_item()
        
        child.name_label.set_markup("<span size='large' weight='bold'>{}</span>".format(
            GLib.markup_escape_text(data.name)))
        child.catalogitemid_label.set_text(data.catalog_item_id)
        child.reason_label.set_markup("<i>{}</i>".format(GLib.markup_escape_text(data.reason)))
        
        if hasattr(child.new_game_button,"_signal_clicked_connector"):
            child.new_game_button.disconnect(child.new_game_button._signal_clicked_connector)
        child.new_game_button._signal_clicked_connector = child.new_game_button.connect('clicked',
                                                                                        self._on_listitem_new_game_button_clicked,
                                                                                        data)
        
        if hasattr(child.remove_button,'_signal_clicked_connector'):
            child.remove_button.disconnect(child.remove_button._signal_clicked_connector)
        child.remove_button._signal_clicked_connector = child.remove_button.connect('clicked',
                                                                                    self._on_listitem_remove_button_clicked,
                                                                                    data)
        
        
    def __remove_ignored_app(self,data:EpicIgnoredApp):
        epic = Epic()
        epic.remove_ignored_app(data)
        
        for i in range(self.__liststore.get_n_items()):
            item = self.__liststore.get_item(i)
            if item.catalog_item_id == data.catalog_item_id:
                self.__liststore.remove(i)
                break
            
    def _on_listitem_new_game_button_clicked(self,button,data:EpicIgnoredApp):
        def on_dialog_response(self,dialog,response,data):
            if response == Gtk.ResponseType.APPLY:
                self.__remove_item(data)
        
            
        game = Game("",data.name,"")
        epic = Epic()
        game_info = epic.find_apps()[data.catalog_item_id]
        
        if PLATFORM_WINDOWS:
            windows = EpicWindowsData("","",installdir=game_info.installdir)
        else:
            windows = None
            
        game.epic = EpicGameData(data.catalog_item_id,windows)
        
        parent = self.get_transient_for()
        dialog=GameDialog(parent=parent,game=game)
        dialog.connect_after('response',on_dialog_response,data)
            
        self.hide()
        dialog.present()
        
    
    def _on_listitem_remove_button_clicked(self,button,data:EpicIgnoredApp):
        epic = Epic()
        self.__remove_ignored_app(data)
        
    def do_response(self,response):
        self.hide()
        self.destroy()
        