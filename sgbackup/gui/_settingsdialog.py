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

from gi.repository import Gtk,GLib,Gio
from gi.repository.GObject import GObject,Signal,Property,SignalFlags,BindingFlags

from ..settings import settings
from ..archiver import ArchiverManager,Archiver
import zipfile

    
class ArchiverSorter(Gtk.Sorter):
    def do_compare(self,item1,item2):
        c1 = item1.name.upper()
        c2 = item2.name.upper()
        
        if (c1 > c2):
            return Gtk.Ordering.LARGER
        elif (c1 < c2):
            return Gtk.Ordering.SMALLER
        else:
            return Gtk.Ordering.EQUAL

class ZipfileCompressorData(GObject):
    def __init__(self,compressor,name,is_standard):
        GObject.__init__(self)
        self.__compressor = compressor
        self.__name = name
        self.__is_standard = is_standard
        
    @Property(type=int)
    def compressor(self)->int:
        return self.__compressor
    
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property(type=bool,default=False)
    def is_standard(self)->bool:
        return self.__is_standard
    
class ZipfileCompressorDataSorter(Gtk.Sorter):
    def do_compare(self,item1:ZipfileCompressorData,item2:ZipfileCompressorData):
        if (item1.name > item2.name):
            return Gtk.Ordering.LARGER
        elif (item1.name < item2.name):
            return Gtk.Ordering.SMALLER
        else:
            return Gtk.Ordering.EQUAL
    

class VariableData(GObject):
    def __init__(self,name:str,value:str):
        GObject.__init__(self)
        self.__name = name
        self.__value = value
        
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @name.setter
    def name(self,name:str):
        self.__name = name
        
    @Property(type=str)
    def value(self)->str:
        return self.__value
    
    @value.setter
    def value(self,value:str):
        self.__value = value
        
class VariableDataSorter(Gtk.Sorter):
    def do_compare(self,item1,item2):
        if (item1.name < item2.name):
            return Gtk.Ordering.SMALLER
        elif (item1.name > item2.name):
            return Gtk.Ordering.LARGER
        else:
            return Gtk.Ordering.EQUAL
        

class SettingsDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self)
        if parent:
            self.set_transient_for(parent)
        self.set_default_size(800,600)
        vbox = self.get_content_area()
        self._widget_set_margin(vbox,4)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(250)
        
        self.__stack = Gtk.Stack()
        self.__stack_sidebar = Gtk.StackSidebar.new()
        self.__general_page = self.__add_general_settings_page()
        self.__archiver_page = self.__add_archiver_settings_page()
        self.__variables_page = self.__add_variables_settings_page()
    
        sidebar_scrolled=Gtk.ScrolledWindow()
        sidebar_scrolled.set_child(self.__stack_sidebar)
        sidebar_scrolled.set_hexpand(True)
        sidebar_scrolled.set_vexpand(True)
        paned.set_start_child(sidebar_scrolled)
        paned.set_end_child(self.__stack)
        paned.set_vexpand(True)
        self.__stack_sidebar.set_stack(self.__stack)
        
        vbox.append(paned)
    
        self.add_button("Apply",Gtk.ResponseType.APPLY)
        self.add_button("Cancel",Gtk.ResponseType.CANCEL)
    
    def create_frame(self,label_text:str):
        label = Gtk.Label()
        label.set_markup("<span weight=\"bold\">{}</span>".format(GLib.markup_escape_text(label_text)))
        frame = Gtk.Frame()
        frame.set_label_widget(label)
        frame.set_margin_start(5)
        frame.set_margin_end(5)
        frame.set_margin_top(5)
        frame.set_margin_bottom(5)
        return frame
    
    def create_grid(self):
        grid = Gtk.Grid()
        grid.set_margin_start(5)
        grid.set_margin_end(5)
        grid.set_margin_top(5)
        grid.set_margin_bottom(5)
        grid.set_column_spacing(3)
        return grid
        
    def create_label(self,label_text:str):
        label = Gtk.Label.new(label_text)
        label.set_xalign(0.0)
        return label
    
    @property
    def general_page(self):
        return self.__general_page
    
    @property
    def archiver_page(self):
        return self.__archiver_page
    
    @property
    def variables_page(self):
        return self.__variables_page
    
    def __add_general_settings_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,8)
        backup_frame = self.create_frame('Backup Settings')
        
        grid = self.create_grid()
        
        label = self.create_label('Backup directory:')
        grid.attach(label,0,0,1,1)
        page.backupdir_label = Gtk.Label.new(settings.backup_dir)
        page.backupdir_label.set_hexpand(True)
        grid.attach(page.backupdir_label,1,0,1,1)
        img = Gtk.Image.new_from_icon_name('document-open-symbolic')
        img.set_pixel_size(16)
        backupdir_button = Gtk.Button()
        backupdir_button.set_child(img)
        backupdir_button.connect('clicked',self._on_backupdir_button_clicked)
        grid.attach(backupdir_button,2,0,1,1)
        
        label = self.create_label('Backup versions:')
        grid.attach(label,0,1,1,1)
        page.backup_versions_spinbutton = Gtk.SpinButton.new_with_range(0,1000,1)
        page.backup_versions_spinbutton.set_hexpand(True)
        page.backup_versions_spinbutton.set_value(settings.backup_versions)
        grid.attach(page.backup_versions_spinbutton,1,1,2,1)
        
        label = self.create_label('Max. Backup Threads:')
        page.backup_threads_spinbutton = Gtk.SpinButton.new_with_range(1,256,1)
        page.backup_threads_spinbutton.set_hexpand(True)
        page.backup_threads_spinbutton.set_value(settings.backup_threads)
        grid.attach(label,0,2,1,1)
        grid.attach(page.backup_threads_spinbutton,1,2,2,1)
        
        label = self.create_label("Archiver:")
        archiver_model = Gio.ListStore.new(Archiver)
        for archiver in ArchiverManager.get_global().archivers.values():
            archiver_model.append(archiver)
        archiver_sort_model = Gtk.SortListModel.new(archiver_model,ArchiverSorter())
        
        archiver_factory = Gtk.SignalListItemFactory()
        archiver_factory.connect('setup',self._on_archiver_factory_setup)
        archiver_factory.connect('bind',self._on_archiver_factory_bind)
        page.archiver_dropdown = Gtk.DropDown(model=archiver_sort_model,factory=archiver_factory)
        page.archiver_dropdown.set_hexpand(True)
        archiver_key = settings.archiver if settings.archiver in ArchiverManager.get_global().archivers else "zipfile"
        
        for i in range(archiver_model.get_n_items()):
            archiver = archiver_model.get_item(i)
            if archiver_key == archiver.key:
                page.archiver_dropdown.set_selected(i)
                break
        grid.attach(label,0,3,1,1)
        grid.attach(page.archiver_dropdown,1,3,2,1)
        backup_frame.set_child(grid)
        vbox.append(backup_frame)
        
        ### Search Settings
        search_frame = self.create_frame('Search Settings')
        search_grid = self.create_grid()
        
        label = self.create_label("Case sensitive search:")
        page.search_casesensitive_switch = Gtk.Switch()
        page.search_casesensitive_switch.set_active(settings.search_case_sensitive)
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL,0)
        hbox.append(Gtk.Label(hexpand=True))
        hbox.append(page.search_casesensitive_switch)
        hbox.set_hexpand(True)
        search_grid.attach(label,0,0,1,1)
        search_grid.attach(hbox,1,0,1,1)
        
        label = self.create_label("Minimum Characters:")
        page.search_minchars_spinbutton = Gtk.SpinButton.new_with_range(1,32,1)
        page.search_minchars_spinbutton.set_value(settings.search_min_chars)
        page.search_minchars_spinbutton.set_hexpand(True)
        search_grid.attach(label,0,1,1,1)
        search_grid.attach(page.search_minchars_spinbutton,1,1,1,1)
        
        label = self.create_label("Maximum Results:")
        page.search_maxresults_spinbutton = Gtk.SpinButton.new_with_range(1,100,1)
        page.search_maxresults_spinbutton.set_value(settings.search_max_results)
        page.search_maxresults_spinbutton.set_hexpand(True)
        search_grid.attach(label,0,2,1,1)
        search_grid.attach(page.search_maxresults_spinbutton,1,2,1,1)
        
        search_frame.set_child(search_grid)        
        vbox.append(search_frame)
        
        ### GUI settings
        gui_frame = self.create_frame('GUI')
        gui_grid = self.create_grid()
        
        label = self.create_label("Automatic close Backup Dialogs?")
        page.gui_autoclose_backup_dialog_switch = Gtk.Switch()
        page.gui_autoclose_backup_dialog_switch.set_active(settings.gui_autoclose_backup_dialog)
        filler = Gtk.Label()
        filler.set_hexpand(True)
        gui_grid.attach(label,0,0,1,1)
        gui_grid.attach(filler,1,0,1,1)
        gui_grid.attach(page.gui_autoclose_backup_dialog_switch,2,0,1,1)
        
        label = self.create_label("Automatic close Restore Dialogs?")
        page.gui_autoclose_restore_dialog_switch = Gtk.Switch()
        page.gui_autoclose_restore_dialog_switch.set_active(settings.gui_autoclose_restore_dialog)
        filler = Gtk.Label()
        filler.set_hexpand(True)
        gui_grid.attach(label,0,1,1,1)
        gui_grid.attach(filler,1,1,1,1)
        gui_grid.attach(page.gui_autoclose_restore_dialog_switch,2,1,1,1)
        
        gui_frame.set_child(gui_grid)
        vbox.append(gui_frame)
        
        ### CLI Settings
        cli_frame = self.create_frame("Command Line Interface")
        cli_grid = self.create_grid()
        label = self.create_label("Pager:")
        page.cli_pager_entry = Gtk.Entry()
        page.cli_pager_entry.set_hexpand(True)
        page.cli_pager_entry.set_text(settings.cli_pager if settings.cli_pager else "")
        cli_grid.attach(label,0,0,1,1)
        cli_grid.attach(page.cli_pager_entry,1,0,1,1)
        
        cli_frame.set_child(cli_grid)
        vbox.append(cli_frame)
        
        page.set_child(vbox)
        self.add_page(page,"general","Generic settings")
        return page
    
    def __add_archiver_settings_page(self):
        page = Gtk.ScrolledWindow()
        page.vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL,4)
        
        grid = self.create_grid()
        
        zf_compressors = [
            (zipfile.ZIP_STORED,"Stored",True),
            (zipfile.ZIP_DEFLATED,"Deflated",True),
            (zipfile.ZIP_BZIP2,"BZip2",False),
            (zipfile.ZIP_LZMA,"LZMA",False),
        ]
        
        zipfile_frame = self.create_frame("ZipFile Archiver")
        label = self.create_label("Compressor:")
        zf_compressor_model = Gio.ListStore.new(ZipfileCompressorData)
        for i in zf_compressors:
            zf_compressor_model.append(ZipfileCompressorData(*i))
        zf_compressor_sort_model = Gtk.SortListModel.new(zf_compressor_model,ZipfileCompressorDataSorter())
        zf_compressor_factory = Gtk.SignalListItemFactory()
        zf_compressor_factory.connect('setup',self._on_zipfile_compressor_setup)
        zf_compressor_factory.connect('bind',self._on_zipfile_compressor_bind)
        page.zf_compressor_dropdown = Gtk.DropDown(model=zf_compressor_sort_model,factory=zf_compressor_factory)
        page.zf_compressor_dropdown.set_hexpand(True)
        c = settings.zipfile_compression
        for i in range(zf_compressor_model.get_n_items()):
            if (c == zf_compressor_model.get_item(i).compressor):
                page.zf_compressor_dropdown.set_selected(i)
                break
        grid.attach(label,0,0,1,1)
        grid.attach(page.zf_compressor_dropdown,1,0,1,1)
        
        label = self.create_label("Compression Level:")
        page.zf_compresslevel_spinbutton = Gtk.SpinButton.new_with_range(0.0,9.0,1.0)
        page.zf_compresslevel_spinbutton.set_value(settings.zipfile_compresslevel)
        page.zf_compresslevel_spinbutton.set_hexpand(True)
        grid.attach(label,0,1,1,1)
        grid.attach(page.zf_compresslevel_spinbutton,1,1,1,1)
        
        zipfile_frame.set_child(grid)
        page.vbox.append(zipfile_frame)
        
        page.set_child(page.vbox)
        self.add_page(page,"zipfile","Archiver Settings")
        return page
    
    def _on_variable_add_button_clicked(self,button):
        variable_model = self.__variables_page.variable_columnview.get_model()
        while hasattr(variable_model,'get_model'):
            variable_model = variable_model.get_model()
        variable_model.append(VariableData("",""))
        
    def __add_variables_settings_page(self):
        page = Gtk.Box.new(Gtk.Orientation.VERTICAL,0)
        
        actions = Gtk.ActionBar()
        icon=Gtk.Image.new_from_icon_name('list-add-symbolic')
        button = Gtk.Button()
        button.set_child(icon)
        button.connect('clicked',self._on_variable_add_button_clicked)
        actions.pack_end(button)
        page.append(actions)
        
        scrolled = Gtk.ScrolledWindow()
        
        model = Gio.ListStore.new(VariableData)
        for vname,vvalue in settings.variables.items():
            model.append(VariableData(vname,vvalue))
                        
        sorted_model = Gtk.SortListModel.new(model,VariableDataSorter())
        
        vname_factory = Gtk.SignalListItemFactory()
        vname_factory.connect('setup',self._on_variable_name_factory_setup)
        vname_factory.connect('bind',self._on_variable_name_factory_bind)
        
        vvalue_factory = Gtk.SignalListItemFactory()
        vvalue_factory.connect('setup',self._on_variable_value_factory_setup)
        vvalue_factory.connect('bind',self._on_variable_value_factory_bind)
        
        selection = Gtk.SingleSelection(model=sorted_model)
        page.variable_columnview = Gtk.ColumnView.new(selection)
        
        vname_column = Gtk.ColumnViewColumn.new("Name",vname_factory)
        vname_column.set_expand(True)
        page.variable_columnview.append_column(vname_column)
        
        vvalue_column = Gtk.ColumnViewColumn.new("Value",vvalue_factory)
        page.variable_columnview.append_column(vvalue_column)
        
        page.variable_columnview.set_vexpand(True)
        scrolled.set_child(page.variable_columnview)
        scrolled.set_hexpand(True)
        page.append(scrolled)
        
        self.add_page(page,"variables","Variables")
        
        return page
        
        
    def _on_variable_name_notify_editing(self,label,param,*data):
        if label.props.editing == False:
            if not label.get_text():
                model = self.__variables_page.variable_columnview.get_model()
                while hasattr(model,'get_model'):
                    model = model.get_model()
                
                for i in reversed(range(model.get_n_items())):
                    if not model.get_item(i).name:
                        model.remove(i)
            
        
    def _on_variable_name_factory_setup(self,factory,item):
        label = Gtk.EditableLabel()
        item.set_child(label)
        
    def _on_variable_name_factory_bind(self,factory,item):
        data = item.get_item()
        label = item.get_child()
        label.set_text(data.name)
        if not hasattr(label,'_property_text_to_name_binding'):
            label._property_text_to_name_binding = label.bind_property('text',data,'name',BindingFlags.DEFAULT)
        if not hasattr(label,'_signal_notify_editing_connection'):
            label._signal_notify_editing_connection = label.connect('notify::editing',self._on_variable_name_notify_editing)
        
        if not data.name:
            label.grab_focus()
            label.start_editing()
        
    def _on_variable_value_factory_setup(self,factory,item):
        label = Gtk.EditableLabel()
        item.set_child(label)
        
    def _on_variable_value_factory_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        label.set_text(data.value)
        if not hasattr(label,'_property_text_to_value_binding'):
            label._property_text_to_value_binding = label.bind_property('text',data,'value',BindingFlags.DEFAULT)
        
    def _on_archiver_factory_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_archiver_factory_bind(self,factory,item):
        label = item.get_child()
        archiver = item.get_item()
        label.set_text(archiver.name)
    
    
    def _on_backupdir_dialog_select_folder(self,dialog,result,*data):
        try:
            dir = dialog.select_folder_finish(result)
            if dir is not None:
                self.general_page.backupdir_label.set_text(dir.get_path())
        except:
            pass
        
    def _on_backupdir_button_clicked(self,button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("sgbackup: Choose backup folder")
        dialog.set_initial_folder(Gio.File.new_for_path(self.general_page.backupdir_label.get_text()))
        dialog.select_folder(self,None,self._on_backupdir_dialog_select_folder)
        
        
    def _on_zipfile_compressor_setup(self,factory,item):
        label = Gtk.Label()
        item.set_child(label)
        
    def _on_zipfile_compressor_bind(self,factory,item):
        label = item.get_child()
        data = item.get_item()
        
        if (not data.is_standard):
            label.set_markup("<span foreground=\"red\">{name}</span>".format(name=GLib.markup_escape_text(data.name)))
        else:
            label.set_text(data.name)
            
    def _widget_set_margin(self,widget:Gtk.Widget,margin:int):
        widget.set_margin_top(margin)
        widget.set_margin_bottom(margin)
        widget.set_margin_start(margin)
        widget.set_margin_end(margin)
        
    def add_page(self,page,name,title):
        self.__stack.add_titled(page,name,title)
        
    def do_response(self,response):
        if response == Gtk.ResponseType.APPLY:
            self.emit('save')
            settings.save()
        self.destroy()
            
    @Signal(name='save',
            flags=SignalFlags.RUN_FIRST,
            return_type=None,
            arg_types=())
    def do_save(self):
        settings.backup_dir = self.general_page.backupdir_label.get_text()
        settings.backup_versions = self.general_page.backup_versions_spinbutton.get_value_as_int()
        settings.backup_threads = self.general_page.backup_threads_spinbutton.get_value_as_int()
        settings.archiver = self.general_page.archiver_dropdown.get_selected_item().key
        settings.gui_autoclose_backup_dialog = self.general_page.gui_autoclose_backup_dialog_switch.get_active()
        settings.gui_autoclose_restore_dialog = self.general_page.gui_autoclose_restore_dialog_switch.get_active()
        settings.search_case_sensitive = self.general_page.search_casesensitive_switch.get_active()
        settings.search_min_chars = self.general_page.search_minchars_spinbutton.get_value_as_int()
        settings.search_max_results = self.general_page.search_maxresults_spinbutton.get_value_as_int()
        settings.zipfile_compression = self.archiver_page.zf_compressor_dropdown.get_selected_item().compressor
        settings.zipfile_compresslevel = self.archiver_page.zf_compresslevel_spinbutton.get_value_as_int()
        
        variables = {}
        variable_model = self.__variables_page.variable_columnview.get_model()
        while hasattr(variable_model,'get_model'):
            variable_model = variable_model.get_model()
        for i in range(variable_model.get_n_items()):
            vdata = variable_model.get_item(i)
            if vdata.name:
                variables[vdata.name] = vdata.value
        settings.variables = variables
        