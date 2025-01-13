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

from gi.repository import Gtk,Gio,GLib
from gi.repository.GObject import GObject,Property,Signal,BindingFlags

from ..steam import Steam,SteamLibrary
import os


class SteamLibrariesDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self)
        self.set_title("sgbackup: Steam Libraries")
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
        
        frame = Gtk.Frame.new("Steam libraries")
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
        
        self.add_button("Apply",Gtk.ResponseType.APPLY)
        self.add_button("Cancel",Gtk.ResponseType.CANCEL)
        
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
        dialog.set_title("sgbackup: Select Steam library path")
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
        dialog.set_title("sgbackup: Change Steam library path")
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
        child.chooser_button.connect('clicked',self._on_list_chooser_button_clicked,child.label)
        child.remove_button.connect('clicked',self._on_list_remove_button_clicked,child.label)
        
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
        

class NewSteamAppsData(GObject):
    def __init__(self,data):
        GObject.__init__(self)
    

class NewSteamAppsDialog(Gtk.Dialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.Dialog.__init__(self)
        self.__steam = Steam()
        