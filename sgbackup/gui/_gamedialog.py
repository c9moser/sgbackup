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

from .. import _import_gtk

from gi.repository import Gio,GLib,Gtk,Pango
from gi.repository.GObject import Property,Signal,GObject,BindingFlags,SignalFlags

from ..game import (
    Game,
    GameData,
    GameFileMatcher,
    GameFileType,
    SavegameType,
    WindowsGame,
    LinuxGame,
    MacOSGame,
    SteamLinuxGame,
    SteamWindowsGame,
    SteamMacOSGame,
    GameManager,
)
    

class GameVariableData(GObject):
    """
    GameVariableData The Gio.ListStore data for Variables.
    """
    
    def __init__(self,name:str,value:str):
        """
        GameVariableData

        :param name: The variable name
        :type name: str
        :param value: The variable value
        :type value: str
        
        Properties
        __________
        .. py:property:: name
            :type: str
            
        .. py:property:: value
            :type: str
        """
        GObject.__init__(self)
        self.name = name
        self.value = value
        
    @Property(type=str)
    def name(self)->str:
        """
        name The variable name.

        :type: str
        """
        return self.__name
    @name.setter
    def name(self,name):
        self.__name = name
        
    @Property(type=str)
    def value(self)->str:
        """
        value The variable value

        :type: str
        """
        return self.__value
    @value.setter
    def value(self,value:str):
        self.__value = value
        
class RegistryKeyData(GObject):
    """
    RegistyKeyData The data for Windows registry keys.
    """
    def __init__(self,regkey:str|None=None):
        """
        RegistryKeyData 

        :param regkey: The registry key ot set, defaults to None
        :type regkey: str | None, optional
        """
        GObject.__init__(self)
        if not regkey:
            self.__regkey = ""
            
    @Property(type=str)
    def regkey(self)->str:
        """
        regkey The registry key to set.

        :type: str
        """
        return self.__regkey
    @regkey.setter
    def regkey(self,key:str):
        self.__regkey = key
        
    def __bool__(self):
        return bool(self.__regkey)


class GameFileTypeData(GObject):
    """ GameFileTypeData The *Gio.Liststore* data for GameFileType *Gtk.DropDown* widgets."""
    def __init__(self,match_type:GameFileType,name:str):
        """
        GameFileTypeData

        :param match_type: The matcher type
        :type match_type: GameFileType
        :param name: The name of the matcher type
        :type name: str
        """
        GObject.__init__(self)
        if not isinstance(match_type,GameFileType):
            raise TypeError("GameFileType")
        self.__match_type = match_type
        self.__name = name
        
    @Property
    def match_type(self)->GameFileType:
        """
        match_type The match type

        :type: GameFileType
        """
        return self.__match_type
    
    @Property(type=str)
    def name(self)->str:
        """
        name The name of the match type.

        :type: str
        """
        return self.__name
 
class SavegameTypeData(GObject):
    """
    SavegameTypeData Holds the data for the SavegameType *Gtk.DropDown*.
    """
    
    def __init__(self,type:SavegameType,name:str,icon_name:str):
        """
        SavegameTypeData 

        :param type: The SavegameType to select.
        :type type: SavegameType
        :param name: The name of the SavegameType.
        :type name: str
        :param icon_name: The Icon name to display for the SavegameType
        :type icon_name: str
        """
        GObject.__init__(self)
        self.__sgtype = type
        self.__name = name
        self.__icon_name = icon_name
    
    @Property
    def savegame_type(self)->SavegameType:
        """
        savegame_type The savegane type to select.

        
        :type: SavegameType
        """
        return self.__sgtype
    
    @Property
    def name(self)->str:
        """
        name The name of the SavegameType

        :type: str
        """
        return self.__name
    
    @Property
    def icon_name(self)->str:
        """
        icon_name The icon name for the savegame type.

        :type: str
        """
        return self.__icon_name
         
 
class GameVariableDialog(Gtk.Dialog):
    """ 
    GameVariableDialog The dialog for setting game variables. 
    
    It is bound to on the GameDialog variable columnviews. This dialog
    will update the given columnview automatically if the response is
    *Gtk.Response.APPLY* and destroy itself on any response.
    
    If not variable is given, this dialog will create a new one
    
    """
    def __init__(self,parent:Gtk.Window,columnview:Gtk.ColumnView,variable:GameVariableData|None=None):
        """
        GameVariableDialog

        :param parent: The parent window (should be a GameDialog instance).
        :type parent: Gtk.Window
        :param columnview: The Columnview to operate on.
        :type columnview: Gtk.ColumnView
        :param variable: The variable to edit, defaults to None
        :type variable: GameVariableData | None, optional
        """
        Gtk.Dialog.__init__(self)
        self.set_transient_for(parent)
        self.set_default_size(600,-1)
        
        self.__columnview = columnview
        
        if variable:
            self.__variable = variable
        else:
            self.__variable = None
        
        grid = Gtk.Grid()
        label = Gtk.Label.new("Name:")
        self.__name_entry = Gtk.Entry()
        self.__name_entry.set_hexpand(True)
        self.__name_entry.connect("changed",self._on_name_entry_changed)
        grid.attach(label,0,0,1,1)
        grid.attach(self.__name_entry,1,0,1,1)
        
        label = Gtk.Label.new("Value")
        self.__value_entry = Gtk.Entry()
        self.__value_entry.set_hexpand(True)
        
        grid.attach(label,0,1,1,1)
        grid.attach(self.__value_entry,1,1,1,1)
        
        self.get_content_area().append(grid)
        
        if self.__variable:
            self.__name_entry.set_text(self.__variable.name)
            self.__value_entry.set_text(self.__variable.value)
        
        self.__apply_button = self.add_button("Apply",Gtk.ResponseType.APPLY)
        self.__apply_button.set_sensitive(bool(self))
        
        self.add_button("Cancel",Gtk.ResponseType.CANCEL)
        
    def __bool__(self):
        name = self.__name_entry.get_text()
        if name:
            if self.__variable and self.__variable.name == name:
                return True
            model = self.__columnview.get_model().get_model()
            for i in range(model.get_n_items()):
                if name == model.get_item(i).name:
                    return False
            return True
        return False
        
    def _on_name_entry_changed(self,entry):
        self.__apply_button.set_sensitive(bool(self))
        
    def do_response(self,response):
        if response == Gtk.ResponseType.APPLY:
            if not bool(self):
                return
            if self.__variable:
                self.__variable.name = self.__name_entry.get_text()
                self.__variable.value = self.__value_entry.get_text()
            else:
                model = self.__columnview.get_model().get_model()
                model.append(GameVariableData(self.__name_entry.get_text(),self.__value_entry.get_text()))
        self.hide()
        self.destroy()

       

class GameDialog(Gtk.Dialog):
    def __init__(self,
                 parent:Gtk.Window|None=None,
                 game:Game|None=None):
        """
        GameDialog This dialog is for setting game config.
        
        The dialog automatically saves the game.

        :param parent: The parent Window, defaults to None
        :type parent: Gtk.Window | None, optional
        :param game: The game to configure, defaults to None
        :type game: Game | None, optional
        """
        
        Gtk.Dialog.__init__(self)
        if (parent):
            self.set_transient_for(parent)
        
        if isinstance(game,Game):
            self.__game = game
        else:
            self.__game = None
        
        self.set_default_size(800,600)
        
        self.__filematch_dropdown_model = Gio.ListStore.new(GameFileTypeData)
        self.__filematch_dropdown_model.append(GameFileTypeData(GameFileType.FILENAME,"Filename"))
        self.__filematch_dropdown_model.append(GameFileTypeData(GameFileType.GLOB,"Glob"))
        self.__filematch_dropdown_model.append(GameFileTypeData(GameFileType.REGEX,"Regular expression"))
            
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(200)
        
        self.__stack = Gtk.Stack.new()
        paned.set_end_child(self.__stack)
        paned.set_hexpand(True)
        paned.set_vexpand(True)
        
        self.__stack_sidebar = Gtk.ListBox()
        self.__stack_sidebar.set_activate_on_single_click(False)
        self.__stack_sidebar.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.__stack_sidebar.connect('selected_rows_changed',self._on_stack_sidebar_selected_rows_changed)
        
        sidebar_scrolled = Gtk.ScrolledWindow()
        sidebar_scrolled.set_child(self.__stack_sidebar)
        paned.set_start_child(sidebar_scrolled)
        
        self.__variable_name_factory = Gtk.SignalListItemFactory()
        self.__variable_name_factory.connect('setup',self._on_variable_name_setup)
        self.__variable_name_factory.connect('bind',self._on_variable_name_bind)
        
        self.__variable_value_factory = Gtk.SignalListItemFactory()
        self.__variable_value_factory.connect('setup',self._on_variable_value_setup)
        self.__variable_value_factory.connect('bind',self._on_variable_value_bind)
        
        self.__add_game_page()
        self.__windows = self.__create_windows_page()
        self.__linux = self.__create_linux_page()
        self.__macos = self.__create_macos_page()
        self.__steam_windows = self.__create_steam_page('steam-windows','Steam Windows')
        self.__steam_linux = self.__create_steam_page('steam-linux','Steam Linux')
        self.__steam_macos = self.__create_steam_page('steam-macos','Steam MacOS')
        
        
        for stack_page in self.__stack.get_pages():
            hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,4)
            label = Gtk.Label.new(stack_page.props.title)
            attrs = Pango.AttrList.new()
            size_attr = Pango.AttrSize.new(14 * Pango.SCALE)
            attrs.insert(size_attr)
            label.set_attributes(attrs)
            icon = Gtk.Image.new_from_icon_name(stack_page.props.icon_name)
            icon.set_pixel_size(20)
            hbox.append(icon)
            hbox.append(label)
            hbox.page_name = stack_page.props.name
            
            self.__stack_sidebar.append(hbox)
            
        
        self.__stack_sidebar.select_row(self.__stack_sidebar.get_row_at_index(0))
        
        self.get_content_area().append(paned)
        self.__apply_button = self.add_button("Apply",Gtk.ResponseType.APPLY)
        self.__apply_button.set_sensitive(False)
        
        self.add_button("Cancel",Gtk.ResponseType.CANCEL)
        
        self.reset()
        
    def __add_game_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        sgtype_data = (
            (SavegameType.UNSET,"Not set","process-stop-symbolic"),
            
            (SavegameType.WINDOWS,"Windows native","windows-svgrepo-com-symbolic"),
            (SavegameType.STEAM_WINDOWS,"Steam Windows","steam-svgrepo-com-symbolic"),
            #(SavegameType.EPIC_WINDOWS,"Epic Windows","object-select-symbolic"),
            #(SavegameType.GOG_WINDOWS,"GoG Windows","object-select-symbolic"),
            
            (SavegameType.LINUX,"Linux native","linux-svgrepo-com-symbolic"),
            (SavegameType.STEAM_LINUX,"Steam Linux","steam-svgrepo-com-symbolic"),
            #(SavegameType.EPIC_LINUX,"Epic Linux","object-select-symbolic"),
            #(SavegameType.GOG_LINUX,"GoG Linux","object-select-symbolic"),
            
            (SavegameType.MACOS,"MacOS native","apple-svgrepo-com-symbolic"),
            (SavegameType.STEAM_MACOS,"Steam MacOS","steam-svgrepo-com-symbolic"),
        )
        sgtype_model = Gio.ListStore.new(SavegameTypeData)
        for data in sgtype_data:
            sgtype_model.append(SavegameTypeData(*data))
            
        grid = Gtk.Grid.new()
        
        label = Gtk.Label.new("Is active?")
        self.__active_switch = Gtk.Switch()
        entry_hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,5)
        entry_hbox.append(self.__active_switch)
        entry_hbox.append(label)
        vbox.append(entry_hbox)
        
        label = Gtk.Label.new("Is live?")
        self.__live_switch = Gtk.Switch()
        entry_hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,5)
        
        entry_hbox.append(self.__live_switch)
        entry_hbox.append(label)
        vbox.append(entry_hbox)
        
        label = Gtk.Label.new("ID:")
        self.__id_label = Gtk.Label()
        self.__id_label.set_hexpand(True)
        grid.attach(label,0,0,1,1)
        grid.attach(self.__id_label,1,0,1,1)
        
        label = Gtk.Label.new("Key:")
        self.__key_entry = Gtk.Entry()
        self.__key_entry.set_hexpand(True)
        self.__key_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        
        grid.attach(label,0,1,1,1)
        grid.attach(self.__key_entry,1,1,1,1)
        
        sgtype_factory = Gtk.SignalListItemFactory()
        sgtype_factory.connect('setup',self._on_savegame_type_setup)
        sgtype_factory.connect('bind',self._on_savegame_type_bind)
        self.__savegame_type_dropdown = Gtk.DropDown(model=sgtype_model,factory=sgtype_factory)
        self.__savegame_type_dropdown.set_selected(0)
        self.__savegame_type_dropdown.set_hexpand(True)
        self.__savegame_type_dropdown.connect('notify::selected-item',lambda w,d: self._on_savegame_type_changed())
        label = Gtk.Label.new("Savegame Type:")
        grid.attach(label,0,2,1,1)
        grid.attach(self.__savegame_type_dropdown,1,2,1,1)
        
        label = Gtk.Label.new("Game name:")
        self.__name_entry = Gtk.Entry()
        self.__name_entry.set_hexpand(True)
        self.__name_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,3,1,1)
        grid.attach(self.__name_entry,1,3,1,1)
        
        label = Gtk.Label.new("Savegame name:")
        self.__sgname_entry = Gtk.Entry()
        self.__sgname_entry.set_hexpand(True)
        self.__sgname_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,4,1,1)
        grid.attach(self.__sgname_entry,1,4,1,1)
        vbox.append(grid)
        
        self.__game_variables = self.__create_variables_widget()
        
        vbox.append(self.__game_variables)
        
        page.set_child(vbox)
        self.__stack.add_titled(page,"main","Game")
        stack_page = self.__stack.get_page(page)
        stack_page.set_icon_name('org.sgbackup.sgbackup-symbolic')
        
        
    def __create_windows_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        grid = Gtk.Grid()
        
        label = Gtk.Label.new("Root directory:")
        page.sgroot_entry = Gtk.Entry()
        page.sgroot_entry.set_hexpand(True)
        page.sgroot_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,0,1,1)
        grid.attach(page.sgroot_entry,1,0,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
        page.sgdir_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,1,1,1)
        grid.attach(page.sgdir_entry,1,1,1,1)
        
        label = Gtk.Label.new("Installation directory:")
        page.installdir_entry = Gtk.Entry()
        page.installdir_entry.set_hexpand(True)
        grid.attach(label,0,2,1,1)
        grid.attach(page.installdir_entry,1,2,1,1)
        vbox.append(grid)
        
        page.filematch = self.__create_filematch_widget('Match Files')
        vbox.append(page.filematch)
        
        page.ignorematch = self.__create_filematch_widget('Ignore Files')
        vbox.append(page.ignorematch)
        
        page.lookup_regkeys = self.__create_registry_key_widget("Lookup Registry keys")
        vbox.append(page.lookup_regkeys)
        
        page.installdir_regkeys = self.__create_registry_key_widget("Installations directory Registry keys")
        vbox.append(page.installdir_regkeys)
        
        page.variables = self.__create_variables_widget()
        vbox.append(page.variables)
        
        page.set_child(vbox)
        self.__stack.add_titled(page,"windows","Windows")
        stack_page = self.__stack.get_page(page)
        stack_page.set_icon_name("windows-svgrepo-com-symbolic")
        
        return page
        
            
    def __create_linux_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        grid = Gtk.Grid()
        label = Gtk.Label.new("Root directory:")
        page.sgroot_entry = Gtk.Entry()
        page.sgroot_entry.set_hexpand(True)
        page.sgroot_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,0,1,1)
        grid.attach(page.sgroot_entry,1,0,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
        page.sgdir_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,1,1,1)
        grid.attach(page.sgdir_entry,1,1,1,1)
        
        label = Gtk.Label.new("Executable")
        page.binary_entry = Gtk.Entry()
        page.binary_entry.set_hexpand(True)
        grid.attach(label,0,2,1,1)
        grid.attach(page.binary_entry,1,2,1,1)
        vbox.append(grid)
        
        page.filematch = self.__create_filematch_widget('Match Files')
        vbox.append(page.filematch)
        
        page.ignorematch = self.__create_filematch_widget('Ignore Files')
        vbox.append(page.ignorematch)
        
        page.variables = self.__create_variables_widget()
        vbox.append(page.variables)
        
        page.set_child(vbox)
        self.__stack.add_titled(page,"linux","Linux")
        stack_page = self.__stack.get_page(page)
        stack_page.set_icon_name("linux-svgrepo-com-symbolic")
        
        return page
    
    def __create_macos_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        grid = Gtk.Grid()
        label = Gtk.Label.new("Root directory:")
        page.sgroot_entry = Gtk.Entry()
        page.sgroot_entry.set_hexpand(True)
        page.sgroot_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,0,1,1)
        grid.attach(page.sgroot_entry,1,0,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
        page.sgdir_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,1,1,1)
        grid.attach(page.sgdir_entry,1,1,1,1)
        
        label = Gtk.Label.new("Executable")
        page.binary_entry = Gtk.Entry()
        page.binary_entry.set_hexpand(True)
        grid.attach(label,0,2,1,1)
        grid.attach(page.binary_entry,1,2,1,1)
        vbox.append(grid)
        
        page.filematch = self.__create_filematch_widget('Match Files')
        vbox.append(page.filematch)
        
        page.ignorematch = self.__create_filematch_widget('Ignore Files')
        vbox.append(page.ignorematch)
        
        page.variables = self.__create_variables_widget()
        vbox.append(page.variables)
        
        page.set_child(vbox)
        self.__stack.add_titled(page,"macos","MacOS")
        stack_page = self.__stack.get_page(page)
        stack_page.set_icon_name("apple-svgrepo-com-symbolic")
        
        return page

    def __create_steam_page(self,name,title):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        grid = Gtk.Grid()
        
        label = Gtk.Label.new("App ID:")
        page.appid_entry = Gtk.Entry()
        page.appid_entry.set_hexpand(True)
        grid.attach(label,0,0,1,1)
        grid.attach(page.appid_entry,1,0,1,1)
                
        label = Gtk.Label.new("Root directory:")
        page.sgroot_entry = Gtk.Entry()
        page.sgroot_entry.set_hexpand(True)
        page.sgroot_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,1,1,1)
        grid.attach(page.sgroot_entry,1,1,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
        page.sgdir_entry.connect('changed',lambda w: self._on_savegame_type_changed())
        grid.attach(label,0,2,1,1)
        grid.attach(page.sgdir_entry,1,2,1,1)
        
        label = Gtk.Label.new("Installation directory:")
        page.installdir_entry = Gtk.Entry()
        page.installdir_entry.set_hexpand(True)
        grid.attach(label,0,3,1,1)
        grid.attach(page.installdir_entry,1,3,1,1)
        vbox.append(grid)
        
        page.filematch = self.__create_filematch_widget('Match Files')
        vbox.append(page.filematch)
        
        page.ignorematch = self.__create_filematch_widget('Ignore Files')
        vbox.append(page.ignorematch)
        
        page.variables = self.__create_variables_widget()
        vbox.append(page.variables)
        
        page.set_child(vbox)
        self.__stack.add_titled(page,name,title)
        stack_page = self.__stack.get_page(page)
        stack_page.set_icon_name("steam-svgrepo-com-symbolic")
        
        return page
    
    def __set_widget_margin(self,widget,margin):
        widget.set_margin_start(margin)
        widget.set_margin_end(margin)
        widget.set_margin_top(margin)
        widget.set_margin_bottom(margin)
        
    def __create_variables_widget(self):
        widget = Gtk.Frame.new("Variables")
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,0)
        
        model = Gio.ListStore.new(GameVariableData)
        selection = Gtk.SingleSelection.new(model)
        selection.set_autoselect(False)
        selection.set_can_unselect(True)
                
        widget.columnview = Gtk.ColumnView.new(selection)
        widget.columnview.set_vexpand(True)
        
        widget.actions = Gtk.ActionBar()
        icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        widget.add_button = Gtk.Button()
        widget.add_button.set_child(icon)
        widget.add_button.connect('clicked',
                                  self._on_variables_add_button_clicked,
                                  widget.columnview)
        widget.actions.pack_start(widget.add_button)
        
        icon = Gtk.Image.new_from_icon_name("document-edit-symbolic")
        widget.edit_button = Gtk.Button()
        widget.edit_button.set_child(icon)
        widget.edit_button.set_sensitive(False)
        widget.edit_button.connect('clicked',
                                   self._on_variables_edit_buton_clicked,
                                   widget.columnview)
        widget.actions.pack_start(widget.edit_button)
        
        icon = Gtk.Image.new_from_icon_name("list-remove-symbolic")
        widget.remove_button = Gtk.Button()
        widget.remove_button.set_child(icon)
        widget.remove_button.set_sensitive(False)
        widget.remove_button.connect('clicked',
                                    self._on_variables_remove_button_clicked,
                                    widget.columnview)
        widget.actions.pack_start(widget.remove_button)
        
        name_column = Gtk.ColumnViewColumn.new("Name",self.__variable_name_factory)
        name_column.set_expand(True)
        widget.columnview.append_column(name_column)
        
        value_column = Gtk.ColumnViewColumn.new("Value",self.__variable_value_factory)
        value_column.set_expand(True)
        widget.columnview.append_column(value_column)
        
        selection.connect('selection-changed',self._on_variable_selection_changed,widget)
        
        vbox.append(widget.actions)
        vbox.append(widget.columnview)
        
        widget.set_child(vbox)
        return widget

    def __create_filematch_dropdown(self,item,widget):
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_filematch_type_dropdown_setup)
        factory.connect('bind',self._on_filematch_type_dropdown_bind)
        
        dropdown = Gtk.DropDown(model=self.__filematch_dropdown_model,factory=factory)
        return dropdown
        
    def __create_filematch_widget(self,title:str):
        widget = Gtk.Frame.new(title)
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        
        widget.actions = Gtk.ActionBar()
        
        widget.add_button = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name('list-add-symbolic')
        widget.add_button.set_child(icon)
        widget.add_button.connect('clicked',self._on_filematch_add_button_clicked,widget)
        widget.actions.pack_start(widget.add_button)
        
        model = Gio.ListStore.new(GameFileMatcher)
        selection = Gtk.SingleSelection.new(model)
        selection.set_autoselect(False)
        selection.set_can_unselect(True)
        
        type_factory = Gtk.SignalListItemFactory()
        type_factory.connect('setup',self._on_filematch_type_setup,widget)
        type_factory.connect('bind',self._on_filematch_type_bind,widget)
        
        value_factory = Gtk.SignalListItemFactory()
        value_factory.connect('setup',self._on_filematch_value_setup,widget)
        value_factory.connect('bind',self._on_filematch_value_bind,widget)
        
        widget.columnview = Gtk.ColumnView.new(selection)
        type_column = Gtk.ColumnViewColumn.new("Matcher",type_factory)
        value_column = Gtk.ColumnViewColumn.new("Match value",value_factory)
        value_column.set_expand(True)
        widget.columnview.append_column(type_column)
        widget.columnview.append_column(value_column)
        
        vbox.append(widget.actions)
        vbox.append(widget.columnview)
        widget.set_child(vbox)
        
        return widget
    
    def __create_registry_key_widget(self,title):
        widget = Gtk.Frame.new(title)
        vbox=Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        
        widget.actions = Gtk.ActionBar()
        icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        button = Gtk.Button.new()
        button.set_child(icon)
        button.connect('clicked',self._on_windows_regkey_add_button_clicked,widget)
        widget.actions.pack_start(button)
        
        model = Gio.ListStore.new(RegistryKeyData)
        selection = Gtk.SingleSelection.new(model)
        selection.set_autoselect(False)
        selection.set_can_unselect(True)
        
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup',self._on_windows_regkey_setup)
        factory.connect('bind',self._on_windows_regkey_bind,widget)
        
        widget.listview = Gtk.ListView.new(selection,factory)
        
        vbox.append(widget.actions)
        vbox.append(widget.listview)
        widget.set_child(vbox)
        
        return widget
    
    @Property(type=bool,default=False)
    def has_game(self)->bool:
        return (self.__game is not None)
    
    def reset(self):
        """
        reset Resets the dialog to the Game set on init or clears the dialog if no Game was set.
        """
        def set_variables(var_widget,vars:dict[str:str]|None):
            model = var_widget.columnview.get_model().get_model()
            model.remove_all()
            if vars:
                for k,v in vars.items():
                    model.append(GameVariableData(str(k),str(v)))
                    
        def set_game_widget_data(widget,data:GameData|None):
            def set_filematch(fm_widget,filematchers:list[GameFileMatcher]):
                model = fm_widget.columnview.get_model().get_model()
                model.remove_all()
                if filematchers:
                    for fm in filematchers:
                        model.append(GameFileMatcher(fm.match_type,fm.match_file))
                
            
                
            widget.sgroot_entry.set_text(data.savegame_root if data else "")
            widget.sgdir_entry.set_text(data.savegame_dir if data else "")
            set_variables(widget.variables,data.variables if data else None)
            set_filematch(widget.filematch,data.file_matchers if data else None)
            set_filematch(widget.ignorematch,data.ignore_matchers if data else None)
            
        self.__active_switch.set_active(self.__game.is_active if self.has_game else True)
        self.__live_switch.set_active(self.__game.is_live if self.has_game  else True)
        self.__name_entry.set_text(self.__game.name if self.has_game else "")
        self.__key_entry.set_text(self.__game.key if self.has_game else "")
        self.__sgname_entry.set_text(self.__game.savegame_name if self.has_game else "")
        set_variables(self.__game_variables,self.__game.variables if self.has_game else None)
        
        if self.has_game:
            model = self.__savegame_type_dropdown.get_model()
            sgtype = self.__game.savegame_type
            for i in range(model.get_n_items()):
                item = model.get_item(i)
                if sgtype == item.savegame_type:
                    self.__savegame_type_dropdown.set_selected(i)
                    break
            
        #windows
        set_game_widget_data(self.__windows,self.__game.windows if self.has_game else None)
        self.__windows.lookup_regkeys.listview.get_model().get_model().remove_all()
        self.__windows.installdir_regkeys.listview.get_model().get_model().remove_all()
        if self.has_game and self.__game.windows:
            grk_model = self.__windows.lookup_regkeys.listview.get_model().get_model()
            irk_model = self.__windows.installdir_regkeys.listview.get_model().get_model()
            for rk in self.__game.windows.game_registry_keys:
                grk_model.append(RegistryKeyData(rk))
                
            #set installdir regkeys
            for rk in self.__game.windows.installdir_registry_keys:
                irk_model.append(RegistryKeyData(rk))
        
        #linux
        set_game_widget_data(self.__linux,self.__game.linux if self.has_game else None)
        self.__linux.binary_entry.set_text(self.__game.linux.binary if self.has_game and self.__game.linux else "")

        #macos
        set_game_widget_data(self.__macos,self.__game.macos if self.__game else None)
        self.__macos.binary_entry.set_text(self.__game.macos.binary if self.has_game and self.__game.macos else "")
        
        #steam windows
        set_game_widget_data(self.__steam_windows,self.__game.steam_windows if self.has_game else None)
        self.__steam_windows.appid_entry.set_text(str(self.__game.steam_windows.appid) 
                                                  if self.has_game and self.__game.steam_windows else "")
        self.__steam_windows.installdir_entry.set_text(self.__game.steam_windows.installdir 
                                                       if self.has_game 
                                                       and self.__game.steam_windows 
                                                       and self.__game.steam_windows.installdir
                                                       else "")
            
        #steam linux
        set_game_widget_data(self.__steam_linux,self.__game.steam_linux if self.has_game else None)
        self.__steam_linux.appid_entry.set_text(str(self.__game.steam_linux.appid) 
                                                if self.has_game and self.__game.steam_linux else "")
        self.__steam_linux.installdir_entry.set_text(self.__game.steam_linux.installdir 
                                                     if self.has_game 
                                                     and self.__game.steam_linux
                                                     and self.__game.steam_linux.installdir 
                                                     else "")
        
        #steam macos
        set_game_widget_data(self.__steam_macos,self.__game.steam_macos if self.has_game else None)
        self.__steam_macos.appid_entry.set_text(str(self.__game.steam_macos.appid) 
                                                if self.has_game and self.__game.steam_macos else "")
        self.__steam_macos.installdir_entry.set_text(self.__game.steam_macos.installdir 
                                                     if self.has_game 
                                                     and self.__game.steam_macos
                                                     and self.__game.steam_macos.installdir
                                                     else "")
        
    # reset()
    
    def save(self):
        """
        save Saves the game configuration to file.
        """
        def get_game_data(widget):
            fm_model = widget.filematch.columnview.get_model().get_model()
            im_model = widget.ignorematch.columnview.get_model().get_model()
            var_model = widget.variables.columnview.get_model().get_model()
            
            filematch = []
            ignorematch = []
            variables = {}
            
            for i in range(fm_model.get_n_items()):
                fm_data = fm_model.get_item(i)
                filematch.append(fm_data)
                
            for i in range(im_model.get_n_items()):
                im_data = im_model.get_item(i)
                ignorematch.append(im_data)
            
            for i in range(var_model.get_n_items()):
                var = var_model.get_item(i)
                variables[var.name] = var.value
                
            return {
                'sgroot': widget.sgroot_entry.get_text(),
                'sgdir': widget.sgdir_entry.get_text(),
                'filematch': filematch,
                'ignorematch': ignorematch,
                'variables': variables,
            }
            
        def get_steam_data(widget):
            conf = get_game_data(widget)
            conf.update({
                'appid': int(widget.appid_entry.get_text()),
                'installdir': widget.installdir_entry.get_text(),
            })
            return conf
            
        if not self.get_is_valid():
            return
        
        variables = {}
        var_model = self.__game_variables.columnview.get_model().get_model()
        for i in range(var_model.get_n_items()):
            var = var_model.get_item(i)
            variables[var.name] = var.value
        key = self.__key_entry.get_text()
        name = self.__name_entry.get_text()
        savegame_name = self.__sgname_entry.get_text()
        savegame_type = self.__savegame_type_dropdown.get_selected_item().savegame_type
        if self.has_game:
            self.__game.key = key
            self.__game.name = name
            self.__game.savegame_type = savegame_type
            self.__game.savegame_name = savegame_name
            self.__game.variables = variables
            self.__game.filename = '.'.join((self.__game.key,'gameconf'))
        else:
            self.__game = Game(key,name,savegame_name)
            self.__game.savegame_type = savegame_type
            self.__game.variables = variables
        
        if self.get_is_valid_savegame_type(SavegameType.WINDOWS):
            data = get_game_data(self.__windows)
            installdir = self.__windows.installdir_entry.get_text()
            grk_model = self.__windows.lookup_regkeys.listview.get_model().get_model()
            irk_model = self.__windows.installdir_regkeys.listview.get_model().get_model()
            grk = []
            irk = []
            
            for i in range(grk_model.get_n_items()):
                item = grk.model.get_item(i)
                if item.regkey:
                    grk.append(item.regkey)
                
            for i in range(irk_model.get_n_items()):
                item = irk.model.get_item(i)
                if item.regkey:
                    irk.append(item.regkey)
            
            if self.__game.windows:
                wg = self.__game.windows
                wg.savegame_root = data['sgroot']
                wg.savegame_dir = data['sgdir']
                wg.variables = data['variables']
                wg.file_match = data["filematch"]
                wg.ignore_match = data['ignorematch']
                wg.installdir = installdir
                wg.game_registry_keys = grk
                wg.installdir_registry_keys = irk
            else:
                self.__game.windows = WindowsGame(data['sgroot'],
                                                  data['sgdir'],
                                                  data['variables'],
                                                  installdir,
                                                  grk,
                                                  irk,
                                                  data['filematch'],
                                                  data['ignorematch'])
        elif self.__game.windows:
            self.__game.windows = None
            
        if self.get_is_valid_savegame_type(SavegameType.LINUX):
            data = get_game_data(self.__linux)
            binary = self.__linux.binary_entry.get_text()
            if self.__game.linux:
                lg = self.__game.linux
                lg.savegame_root = data['sgroot']
                lg.savegame_dir = data['sgdir']
                lg.variables = data['variables']
                lg.file_match = data["filematch"]
                lg.ignore_match = data['ignorematch']
                lg.binary = binary
            else:
                self.__game.linux = LinuxGame(data["sgroot"],
                                              data['sgdir'],
                                              data["variables"],
                                              binary,
                                              data["filematch"],
                                              data['ignorematch'])
        elif self.__game.linux:
            self.__game_linux = None
            
        if self.get_is_valid_savegame_type(SavegameType.MACOS):
            data = get_game_data(self.__linux)
            binary = self.__linux.binary_entry.get_text()
            if self.__game.linux:
                mg = self.__game.macos
                mg.savegame_root = data['sgroot']
                mg.savegame_dir = data['sgdir']
                mg.variables = data['variables']
                mg.file_match = data["filematch"]
                mg.ignore_match = data['ignorematch']
                mg.binary = binary
            else:
                self.__game.macos = MacOSGame(data["sgroot"],
                                              data['sgdir'],
                                              data["variables"],
                                              binary,
                                              data["filematch"],
                                              data['ignorematch'])
        elif self.__game.macos:
            self.__game.macos = None
            
        if self.get_is_valid_savegame_type(SavegameType.STEAM_WINDOWS):
            data = get_steam_data(self.__steam_windows)
            if self.__game.steam_windows:
                sg = self.__game.steam_windows
                sg.savegame_root = data['sgroot']
                sg.savegame_dir = data['sgdir']
                sg.variables = data['variables']
                sg.file_match = data["filematch"]
                sg.ignore_match = data['ignorematch']
                sg.appid = data['appid']
                sg.installdir = data['installdir']
            else:
                self.__game.steam_windows = SteamWindowsGame(data['appid'],
                                                             data['sgroot'],
                                                             data['sgdir'],
                                                             data['variables'],
                                                             data['installdir'],
                                                             data['filematch'],
                                                             data['ignorematch'])
        elif self.__steam_windows:
            self.__steam_windows = None
                
        if self.get_is_valid_savegame_type(SavegameType.STEAM_LINUX):
            data = get_steam_data(self.__steam_linux)
            if self.__game.steam_linux:
                sg = self.__game.steam_linux
                sg.savegame_root = data['sgroot']
                sg.savegame_dir = data['sgdir']
                sg.variables = data['variables']
                sg.file_match = data["filematch"]
                sg.ignore_match = data['ignorematch']
                sg.appid = data['appid']
                sg.installdir = data['installdir']
            else:
                self.__game.steam_linux = SteamLinuxGame(data['appid'],
                                                         data['sgroot'],
                                                         data['sgdir'],
                                                         data['variables'],
                                                         data['installdir'],
                                                         data['filematch'],
                                                         data['ignorematch'])
        elif self.__steam_linux:
            self.__steam_linux = None
            
        if self.get_is_valid_savegame_type(SavegameType.STEAM_MACOS):
            data = get_steam_data(self.__steam_macos)
            if self.__game.steam_macos:
                sg = self.__game.steam_macos
                sg.savegame_root = data['sgroot']
                sg.savegame_dir = data['sgdir']
                sg.variables = data['variables']
                sg.file_match = data["filematch"]
                sg.ignore_match = data['ignorematch']
                sg.appid = data['appid']
                sg.installdir = data['installdir']
            else:
                self.__game.steam_macos = SteamMacOSGame(data['appid'],
                                                         data['sgroot'],
                                                         data['sgdir'],
                                                         data['variables'],
                                                         data['installdir'],
                                                         data['filematch'],
                                                         data['ignorematch'])
        elif self.__steam_macos:
            self.__steam_macos = None
            
        self.__game.save()
        GameManager.get_global().add_game(self.__game)
                
        
    def get_is_valid(self)->bool:
        """
        get_is_valid Check if the configuration is valid for saving.
        
        :returns: `True` if the game data is valid.
        :rtype: bool
        """
        
        if (self.__key_entry.get_text() and self.__name_entry.get_text() and self.__sgname_entry.get_text()):
            sgtype_data = self.__savegame_type_dropdown.get_selected_item()
            return self.get_is_valid_savegame_type(sgtype_data.savegame_type)
        return False
    
    def get_is_valid_savegame_type(self,sgtype:SavegameType)->bool:
        """
        get_is_valid_savegame_type Check if the data for a SavegameType savegame is valid.
        
        :param sgtype: The type of the Savegame provider
        :type: sgbackup.game.SavegameType
        :returns: bool
        """
        
        def check_is_valid(widget):
            return (bool(widget.sgroot_entry.get_text()) and bool(widget.sgdir_entry.get_text()))
        
        if sgtype == SavegameType.WINDOWS:
            return check_is_valid(self.__windows)
        elif sgtype == SavegameType.LINUX:
            return check_is_valid(self.__linux)
        elif sgtype == SavegameType.MACOS:
            return check_is_valid(self.__macos)
        elif sgtype == SavegameType.STEAM_WINDOWS:
            return check_is_valid(self.__steam_windows)
        elif sgtype == SavegameType.STEAM_LINUX:
            return check_is_valid(self.__steam_linux)
        elif sgtype == SavegameType.STEAM_MACOS:
            return check_is_valid(self.__steam_macos)
        #elif sgtype == SavegameType.EPIC_WINDOWS:
        #    return check_is_valid(self.__epic_windows)
        #elif sgtype == SavegameType.EPIC_LINUX:
        #    return check_is_valid(self.__epic_linux)
        #elif sgtype == SavegameType.GOG_WINDOWS:
        #    return check_is_valid(self.__gog_windows)
        #elif sgtype == SavegameType.GOG_LINUX:
        #    return check_is_valid(self.__gog_linux)
        return False
        
    def _on_savegame_type_setup(self,factory,item):
        vbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,4)
        vbox.icon = Gtk.Image()
        vbox.label = Gtk.Label()
        
        vbox.append(vbox.icon)
        vbox.append(vbox.label)
        item.set_child(vbox)
        
    def _on_savegame_type_bind(self,factory,item):
        vbox = item.get_child()
        data = item.get_item()
        vbox.icon.props.icon_name = data.icon_name
        vbox.label.set_text(data.name)
        
    def _on_savegame_type_changed(self):
        self.__apply_button.set_sensitive(self.get_is_valid())
        
    def _on_variable_name_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_variable_name_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        data.bind_property('name',label,'label',BindingFlags.SYNC_CREATE)
        
    def _on_variable_value_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_variable_value_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        data.bind_property('value',label,'label',BindingFlags.SYNC_CREATE)
        
    def _on_filematch_dropdown_selection_changed(self,dropdown,data,item):
        data = item.get_item()
        data.match_type = dropdown.get_selected_item().match_type
    
    def _on_filematch_type_dropdown_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)                
    
    def _on_filematch_type_dropdown_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_text(data.name)
            
    def _on_filematch_type_setup(self,factory,item,widget):
        item.set_child(self.__create_filematch_dropdown(item,widget))
    
    def _on_filematch_type_bind(self,factory,item,widget):
        dropdown = item.get_child()
        data = item.get_item()
        for i in range(self.__filematch_dropdown_model.get_n_items()):
            if (data.match_type == self.__filematch_dropdown_model.get_item(i).match_type):
                dropdown.set_selected(i)
                break
        dropdown.connect('notify::selected-item',self._on_filematch_dropdown_selection_changed,item)
        
    def _on_filematch_value_setup(self,factory,item,widget):
        label = Gtk.EditableLabel()
        item.set_child(label)
    
    def _on_filematch_value_bind(self,factory,item,widget):
        label = item.get_child()
        data = item.get_item()
        if (data.match_file):
            label.set_text(data.match_file)
            label.bind_property('text',data,'match_file',BindingFlags.DEFAULT)
            #label.connect('changed',self._on_filematch_value_label_changed,widget)
            label.connect('notify::editing',self._on_filematch_value_notify_editing,widget)
        else:
            label.bind_property('text',data,'match_file',BindingFlags.DEFAULT)
            #label.connect('changed',self._on_filematch_value_label_changed,widget)
            label.connect('notify::editing',self._on_filematch_value_notify_editing,widget)
            label.grab_focus()
            label.start_editing()
            
        
    
    def _on_windows_regkey_setup(self,factory,item):
        label = Gtk.EditableLabel()
        item.set_child(label)
        
    def _on_windows_regkey_bind(self,factory,item,widget):
        label = item.get_child()
        data = item.get_item()
        label.set_text(data.regkey)
        label.bind_property('text',data,'regkey',GObject.BindingFlags.DEFAULT)
        label.connect('changed',self._on_windows_regkey_label_changed,widget)
        if not label.get_text():
            label.start_editing()
            label.grab_focus()
            
    def _on_stack_sidebar_selected_rows_changed(self,sidebar):
        row = sidebar.get_selected_row()
        self.__stack.set_visible_child_name(row.get_child().page_name)
        
    def _on_variables_add_button_clicked(self,button,columnview):
        dialog = GameVariableDialog(self,columnview)
        dialog.present()
        
    def _on_variables_remove_button_clicked(self,button,columnview):
        selection = columnview.get_model()
        model = selection.get_model()
        selected = selection.get_selected()
        if selected == Gtk.INVALID_LIST_POSITION:
            return
        model.remove(selected)
    
    def _on_variables_edit_buton_clicked(self,button,columnview):
        data = columnview.get_model().get_selected()
        if data:
            dialog = GameVariableDialog(self,columnview,data)
            dialog.present()
    
    def _on_variable_selection_changed(self,selection,position,n_items,var_widget):
        if (selection.get_model().get_n_items() == 0) or (selection.get_selected() == Gtk.INVALID_LIST_POSITION):
            var_widget.edit_button.set_sensitive(False)
            var_widget.remove_button.set_sensitive(False)
        else:
            var_widget.edit_button.set_sensitive(True)
            var_widget.remove_button.set_sensitive(True)
    
    def _on_filematch_add_button_clicked(self,button,widget):
        widget.columnview.get_model().get_model().append(GameFileMatcher(GameFileType.GLOB,""))
    
    def _on_filematch_value_label_changed(self,label,widget):
        if not label.get_text().strip():
            model = widget.columnview.get_model().get_model()
            i = 0
            while i < model.get_n_items():
                item = model.get_item(i)
                if not item.match_file.strip():
                    model.remove(i)
                    continue
                i += 1
    def _on_filematch_value_notify_editing(self,label,param,widget):
        if label.props.editing == False:
            if not label.get_text().strip():
                model = widget.columnview.get_model().get_model()
                i = 0
                while i < model.get_n_items():
                    item = model.get_item(i)
                    if not item.match_file.strip():
                        model.remove(i)
                        continue
                    i += 1
                
    def _on_windows_regkey_add_button_clicked(self,button,widget):
        widget.listview.get_model().get_model().append(RegistryKeyData())
        
    def _on_windows_regkey_label_changed(self,label,widget):
        if not label.get_text():
            model = widget.listview.get_model().get_model()
            i = 0
            while i < model.get_n_items():
                item = model.get_item(i)
                if not item.regkey:
                    model.remove(i)
                    continue
                i += 1

    def do_response(self,response):
        if (response == Gtk.ResponseType.APPLY):
            self.save()
            self.emit('apply')
            
        self.hide()
        self.destroy()
        
    @Signal(name='apply',flags=SignalFlags.RUN_FIRST,return_type=None,arg_types=())
    def do_apply(self):
        pass
