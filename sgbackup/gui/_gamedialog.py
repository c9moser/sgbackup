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

from gi.repository import GObject,Gio,GLib,Gtk,Pango
from ..game import (
    Game,
    GameFileMatcher,
    GameFileType,
    SavegameType,
    WindowsGame,
    LinuxGame,
    MacOSGame,
    SteamLinuxGame,
    SteamWindowsGame,
    SteamMacOSGame,
)
    

class GameVariableData(GObject.GObject):
    def __init__(self,name:str,value:str):
        GObject.GObject.__init__(self)
        self.name = name
        self.value = value
        
    @GObject.Property(type=str)
    def name(self)->str:
        return self.__name
    @name.setter
    def name(self,name):
        self.__name = name
        
    @GObject.Property(type=str)
    def value(self)->str:
        return self.__value
    @value.setter
    def value(self,value:str):
        self.__value = value
        
class RegistryKeyData(GObject.GObject):
    def __init__(self,regkey=None):
        GObject.GObject.__init__(self)
        if not regkey:
            self.__regkey = ""
            
    @GObject.Property(type=str)
    def regkey(self):
        return self.__regkey
    @regkey.setter
    def regkey(self,key:str):
        self.__regkey = key
        
    def __bool__(self):
        return bool(self.__regkey)

class GameFileMatcherData(GObject.GObject):
    def __init__(self,match_type:GameFileType,match_value:str):
        GObject.GObject.__init__(self)
        self.match_type = match_type
        self.match_value = match_value
        
    @GObject.Property
    def match_type(self)->GameFileType:
        return self.__match_type
    @match_type.setter
    def match_type(self,type:GameFileType):
        self.__match_type = type
        
    @GObject.Property(type=str)
    def match_value(self)->str:
        return self.__match_value
    @match_value.setter
    def match_value(self,value:str):
        self.__match_value = value

class GameFileTypeData(GObject.GObject):
    def __init__(self,match_type:GameFileType,name:str):
        GObject.GObject.__init__(self)
        self.__match_type = match_type
        self.__name = name
        
    @GObject.Property
    def match_type(self)->GameFileType:
        return self.__match_type
    
    @GObject.Property(type=str)
    def name(self)->str:
        return self.__name
 
class SavegameTypeData(GObject.GObject):
    def __init__(self,type:SavegameType,name:str,icon_name:str):
        GObject.GObject.__init__(self)
        self.__sgtype = type
        self.__name = name
        self.__icon_name = icon_name
    
    @GObject.Property
    def savegame_type(self):
        return self.__sgtype
    
    @GObject.Property
    def name(self):
        return self.__name
    
    @GObject.Property
    def icon_name(self)->str:
        return self.__icon_name
         
 
class GameVariableDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window,columnview:Gtk.ColumnView,variable:GameVariableData|None=None):
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
                 game:Game|None=Game):
        
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
            
        self.reset()
        self.__stack_sidebar.select_row(self.__stack_sidebar.get_row_at_index(0))
        
        self.get_content_area().append(paned)
        self.add_button("Apply",Gtk.ResponseType.APPLY)
        self.add_button("Cancel",Gtk.ResponseType.CANCEL)
        
        
    def __add_game_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        sgtype_data = (
            (SavegameType.UNSET,"Not set","process-stop-symbolic"),
            (SavegameType.WINDOWS,"Windows native","windows-svgrepo-com-symbolic"),
            (SavegameType.LINUX,"Linux native","linux-svgrepo-com-symbolic"),
            (SavegameType.MACOS,"MacOS native","apple-svgrepo-com-symbolic"),
            (SavegameType.STEAM_WINDOWS,"Steam Windows","steam-svgrepo-com-symbolic"),
            (SavegameType.STEAM_LINUX,"Steam Linux","steam-svgrepo-com-symbolic"),
            (SavegameType.STEAM_MACOS,"Steam MacOS","steam-svgrepo-com-symbolic"),
            #(SavegameType.EPIC_WINDOWS,"Epic Windows","object-select-symbolic"),
            #(SavegameType.EPIC_LINUX,"Epic Linux","object-select-symbolic"),
            #(SavegameType.GOG_WINDOWS,"GoG Windows","object-select-symbolic"),
            #(SavegameType.GOG_LINUX,"GoG Linux","object-select-symbolic"),
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
        grid.attach(label,0,1,1,1)
        grid.attach(self.__key_entry,1,1,1,1)
        
        sgtype_factory = Gtk.SignalListItemFactory()
        sgtype_factory.connect('setup',self._on_savegame_type_setup)
        sgtype_factory.connect('bind',self._on_savegame_type_bind)
        self.__savegame_type_dropdown = Gtk.DropDown(model=sgtype_model,factory=sgtype_factory)
        self.__savegame_type_dropdown.set_selected(0)
        self.__savegame_type_dropdown.set_hexpand(True)
        label = Gtk.Label.new("Savegame Type:")
        grid.attach(label,0,2,1,1)
        grid.attach(self.__savegame_type_dropdown,1,2,1,1)
        
        label = Gtk.Label.new("Game name:")
        self.__name_entry = Gtk.Entry()
        self.__name_entry.set_hexpand(True)
        grid.attach(label,0,3,1,1)
        grid.attach(self.__name_entry,1,3,1,1)
        
        label = Gtk.Label.new("Savegame name:")
        self.__sgname_entry = Gtk.Entry()
        self.__sgname_entry.set_hexpand(True)
        grid.attach(label,0,4,1,1)
        grid.attach(self.__sgname_entry,1,4,1,1)
        vbox.append(grid)
        
        self.__game_variables = self.__create_variables_widget()
        
        vbox.append(self.__game_variables)
        
        page.set_child(vbox)
        self.__stack.add_titled(page,"main","Game")
        stack_page = self.__stack.get_page(page)
        stack_page.set_icon_name('sgbackup')
        
        
    def __create_windows_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,2)
        self.__set_widget_margin(vbox,5)
        
        grid = Gtk.Grid()
        
        label = Gtk.Label.new("Root directory:")
        page.sgroot_entry = Gtk.Entry()
        page.sgroot_entry.set_hexpand(True)
        grid.attach(label,0,0,1,1)
        grid.attach(page.sgroot_entry,1,0,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
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
        grid.attach(label,0,0,1,1)
        grid.attach(page.sgroot_entry,1,0,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
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
        grid.attach(label,0,0,1,1)
        grid.attach(page.sgroot_entry,1,0,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
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
        grid.attach(label,0,1,1,1)
        grid.attach(page.sgroot_entry,1,1,1,1)
        
        label = Gtk.Label.new("Backup directory:")
        page.sgdir_entry = Gtk.Entry()
        page.sgdir_entry.set_hexpand(True)
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
        
        model = Gio.ListStore.new(GameFileMatcherData)
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
    
    def reset(self):
        self.__active_switch.set_active(True)
        self.__live_switch.set_active(True)
        self.__name_entry.set_text("")
        self.__sgname_entry.set_text("")
        self.__game_variables.columnview.get_model().get_model().remove_all()
            
        #windows
        self.__windows.sgroot_entry.set_text("")
        self.__windows.sgdir_entry.set_text("")
        self.__windows.variables.columnview.get_model().get_model().remove_all()
        self.__windows.filematch.columnview.get_model().get_model().remove_all()
        self.__windows.ignorematch.columnview.get_model().get_model().remove_all()
        self.__windows.lookup_regkeys.listview.get_model().get_model().remove_all()
        self.__windows.installdir_regkeys.listview.get_model().get_model().remove_all()
        
        #linux
        self.__linux.sgroot_entry.set_text("")
        self.__linux.sgdir_entry.set_text("")
        self.__linux.binary_entry.set_text("")
        self.__linux.filematch.columnview.get_model().get_model().remove_all()
        self.__linux.ignorematch.columnview.get_model().get_model().remove_all()
        self.__linux.variables.columnview.get_model().get_model().remove_all()
        
        #linux
        self.__macos.sgroot_entry.set_text("")
        self.__macos.sgdir_entry.set_text("")
        self.__macos.binary_entry.set_text("")
        self.__macos.filematch.columnview.get_model().get_model().remove_all()
        self.__macos.ignorematch.columnview.get_model().get_model().remove_all()
        self.__macos.variables.columnview.get_model().get_model().remove_all()
        
        #steam windows
        self.__steam_windows.sgroot_entry.set_text("")
        self.__steam_windows.sgdir_entry.set_text("")
        self.__steam_windows.appid_entry.set_text("")
        self.__steam_windows.installdir_entry.set_text("")
        self.__steam_windows.filematch.columnview.get_model().get_model().remove_all()
        self.__steam_windows.ignorematch.columnview.get_model().get_model().remove_all()
        self.__steam_windows.variables.columnview.get_model().get_model().remove_all()
            
        #steam linux
        self.__steam_linux.sgroot_entry.set_text("")
        self.__steam_linux.sgdir_entry.set_text("")
        self.__steam_linux.appid_entry.set_text("")
        self.__steam_linux.installdir_entry.set_text("")
        self.__steam_linux.filematch.columnview.get_model().get_model().remove_all()
        self.__steam_linux.ignorematch.columnview.get_model().get_model().remove_all()
        self.__steam_linux.variables.columnview.get_model().get_model().remove_all()
        
        #steam macos
        self.__steam_macos.sgroot_entry.set_text("")
        self.__steam_macos.sgdir_entry.set_text("")
        self.__steam_macos.appid_entry.set_text("")
        self.__steam_macos.installdir_entry.set_text("")
        self.__steam_macos.filematch.columnview.get_model().get_model().remove_all()
        self.__steam_macos.ignorematch.columnview.get_model().get_model().remove_all()
        self.__steam_macos.variables.columnview.get_model().get_model().remove_all()
        
        if self.__game:
            self.__active_switch.set_active(self.__game.is_active)
            self.__live_switch.set_active(self.__game.is_live)
            self.__name_entry.set_text(self.__game.name)
            self.__sgname_entry.set_text(self.__game.savegame_name)
            for name,value in self.__game.variables.items():
                self.__game_variables.get_model().get_model().append(GameVariableData(name,value))
                
            if self.__game.windows:
                self.__windows.sgroot_entry.set_text(self.__game.windows.savegame_root)
                self.__windows.sgdir_entry.set_text(self.__game.windows.savegame_dir)
                self.__windows.installdir_entry.set_text(self.__game.windows.installdir)
                
                #filematch
                fm_model = self.__windows.filematch.columnview.get_model().get_model()
                for fm in self.__game.windows.filematch:
                    fm_model.append(GameFileMatcherData(fm.match_type,fm.match_file))
                
                im_model = self.__windows.ignorematch.columnview.get_model().get_model()
                for im in self.__game.windows.ignorematch:
                    im_model.append(GameFileMatcherData(im.match_type,im.match_file))
                    
                # set lookup regkeys
                var_model = self.__windows.variables.columnview.get_model().get_model()
                grk_model = self.__windows.lookup_regkeys.listview.get_model().get_model()
                irk_model = self.__windows.installdir_regkeys.listview.get_model().get_model()
                for rk in self.__game.windows.game_registry_keys:
                    grk_model.append(RegistryKeyData(rk))
                
                #set installdir regkeys
                for rk in self.__game.windows.installdir_registry_keys:
                    irk_model.append(RegistryKeyData(rk))
                
                #set variables
                for name,value in self.__game.windows.variables.items():
                    var_model.append(GameVariableData(name,value))
            
            if self.__game.linux:
                self.__linux.sgroot_entry.set_text(self.__game.linux.savegame_root)
                self.__linux.sgdir_entry.set_text(self.__game.linux.savegame_dir)
                self.__linux.binary_entry.set_text(self.__game.linux.binary)
                
                #filematch
                fm_model = self.__linux.filematch.columnview.get_model().get_model()
                for fm in self.__game.linux.filematch:
                    fm_model.append(GameFileMatcherData(fm.match_type,fm.match_file))
                
                im_model = self.__linux.ignorematch.columnview.get_model().get_model()
                for im in self.__game.linux.ignorematch:
                    im_model.append(GameFileMatcherData(im.match_type,im.match_file))
                
                var_model = self.__linux.variables.columnview.get_model().get_model()
                for name,value in self.__game.linux.variables.items():
                    var_model.append(GameVariableData(name,value))
                    
            if self.__game.macos:
                self.__macos.sgroot_entry.set_text(self.__game.linux.savegame_root)
                self.__macos.sgdir_entry.set_text(self.__game.linux.savegame_dir)
                self.__macos.binary_entry.set_text(self.__game.linux.binary)
                
                #filematch
                fm_model = self.__macos.filematch.columnview.get_model().get_model()
                for fm in self.__game.macos.filematch:
                    fm_model.append(GameFileMatcherData(fm.match_type,fm.match_file))
                
                im_model = self.__macos.ignorematch.columnview.get_model().get_model()
                for im in self.__game.macos.ignorematch:
                    im_model.append(GameFileMatcherData(im.match_type,im.match_file))
                
                var_model = self.__macos.variables.columnview.get_model().get_model()
                for name,value in self.__game.linux.variables.items():
                    var_model.append(GameVariableData(name,value))
                    
            if self.__game.steam_windows:
                self.__steam_windows.sgroot_entry.set_text(self.__game.steam_windows.savegame_root)
                self.__steam_windows.sgdir_entry.set_text(self.__game.steam_windows.savegame_dir)
                self.__steam_windows.appid_entry.set_text(self.__game.steam_windows.appid)
                self.__steam_windows.installdir_entry.set_text(self.__game.steam_windows.installdir)
                
                #filematch
                fm_model = self.__steam_windows.filematch.columnview.get_model().get_model()
                for fm in self.__game.steam_windows.filematch:
                    fm_model.append(GameFileMatcherData(fm.match_type,fm.match_file))
                
                im_model = self.__steam_windows.ignorematch.columnview.get_model().get_model()
                for im in self.__game.steam_windows.ignorematch:
                    im_model.append(GameFileMatcherData(im.match_type,im.match_file))
                
                var_model = self.__steam_windows.variables.columnview.get_model().get_model()
                for name,value in self.__game.steam_windows.variables.items():
                    var_model.append(GameVariableData(name,value))
            
            if self.__game.steam_linux:
                self.__steam_linux.sgroot_entry.set_text(self.__game.steam_linux.savegame_root)
                self.__steam_linux.sgdir_entry.set_text(self.__game.steam_linux.savegame_dir)
                self.__steam_linux.appid_entry.set_text(self.__game.steam_linux.appid)
                self.__steam_linux.installdir_entry.set_text(self.__game.steam_linux.installdir)
                
                fm_model = self.__steam_linux.filematch.columnview.get_model().get_model()
                for fm in self.__game.steam_linux.filematch:
                    fm_model.append(GameFileMatcherData(fm.match_type,fm.match_file))
                
                im_model = self.__steam_linux.ignorematch.columnview.get_model().get_model()
                for im in self.__game.steam_linux.ignorematch:
                    im_model.append(GameFileMatcherData(im.match_type,im.match_file))
                    
                var_model = self.__steam_linux.variables.columnview.get_model().get_model()
                for name,value in self.__game.steam_linux.variables.items():
                    var_model.append(GameVariableData(name,value))
        
            if self.__game.steam_macos:
                self.__steam_macos.sgroot_entry.set_text(self.__game.steam_macos.savegame_root)
                self.__steam_macos.sgdir_entry.set_text(self.__game.steam_macos.savegame_dir)
                self.__steam_macos.appid_entry.set_text(self.__game.steam_macos.appid)
                self.__steam_macos.installdir_entry.set_text(self.__game.steam_macos.installdir)
                
                fm_model = self.__steam_macos.filematch.columnview.get_model().get_model()
                for fm in self.__game.steam_macos.filematch:
                    fm_model.append(GameFileMatcherData(fm.match_type,fm.match_file))
                
                im_model = self.__steam_macos.ignorematch.columnview.get_model().get_model()
                for im in self.__game.steam_macos.ignorematch:
                    im_model.append(GameFileMatcherData(im.match_type,im.match_file))
                    
                var_model = self.__steam_macos.variables.columnview.get_model().get_model()
                for name,value in self.__game.steam_macos.variables.items():
                    var_model.append(GameVariableData(name,value))
    # reset()
    
    def save(self):
        def get_steam_data(widget):
            variables = {}
            var_model = self.__game_variables.get_model().get_model()
            for i in range(var_model.get_n_items()):
                var = var_model.get_item(i)
                variables[var.name] = var.value
                
            if self.__game:
                self.__game.key = self.__key_entry.get_text()
                self.__game.name = self.__name_entry.get_text()
                self.__game.savegame_name = self.__sgname_entry.get_text()
                self.__game.variables = variables
            else:
                pass
                
            #self.__game.save()
        
    def get_is_valid_savegame_type(self,sgtype:SavegameType)->bool:
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
        
    def _on_savegame_type_changed(self,dropdown,data):
        pass
        
        
    def _on_variable_name_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_variable_name_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        data.bind_property('name',label,'label',GObject.BindingFlags.SYNC_CREATE)
        
    def _on_variable_value_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_variable_value_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        data.bind_property('value',label,'label',GObject.BindingFlags.SYNC_CREATE)
        
    def _on_filematch_dropdown_selection_changed(self,dropdown,data,item):
        data = item.get_item()
        data.match_type = dropdown.get_slected_item()
    
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
        if (data.match_value):
            label.set_text(data.match_value)
        else:
            label.start_editing()
            label.grab_focus()
        label.bind_property('text',data,'match_value',GObject.BindingFlags.DEFAULT)
        label.connect('changed',self._on_filematch_value_label_changed,widget)
    
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
        widget.columnview.get_model().get_model().append(GameFileMatcherData(GameFileType.GLOB,""))
    
    def _on_filematch_value_label_changed(self,label,widget):
        if not label.get_text():
            model = widget.columnview.get_model().get_model()
            i = 0
            while i < model.get_n_items():
                item = model.get_item(i)
                if not item.match_value:
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
        