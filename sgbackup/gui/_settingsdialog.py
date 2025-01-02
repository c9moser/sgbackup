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

from gi.repository import Gtk,GLib,Gio
from gi.repository.GObject import GObject,Signal,Property

from ..settings import settings

class SettingsDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self)
        if parent:
            self.set_transient_for(parent)
        self.set_default_size(800,600)
        vbox = self.get_content_area()
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(250)
        
        self.__stack = Gtk.Stack()
        self.__stack_sidebar = Gtk.StackSidebar.new()
        self.__add_general_settings_page()
        
        paned.set_start_child(self.__stack_sidebar)
        paned.set_end_child(self.__stack)
        paned.set_vexpand(True)
        self.__stack_sidebar.set_stack(self.__stack)
        
        vbox.append(paned)
    
        self.add_button("Apply",Gtk.ResponseType.APPLY)
        self.add_button("Cancel",Gtk.ResponseType.CANCEL)
    
    def __add_general_settings_page(self):
        page = Gtk.ScrolledWindow()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        grid = Gtk.Grid()
        
        label = Gtk.Label.new('Backup directory: ')
        grid.attach(label,0,0,1,1)
        self.__backupdir_label = Gtk.Label.new(settings.backup_dir)
        self.__backupdir_label.set_hexpand(True)
        grid.attach(self.__backupdir_label,1,0,1,1)
        img = Gtk.Image.new_from_icon_name('document-open-symbolic')
        img.set_pixel_size(16)
        backupdir_button = Gtk.Button()
        backupdir_button.set_child(img)
        backupdir_button.connect('clicked',self._on_backupdir_button_clicked)
        grid.attach(backupdir_button,2,0,1,1)
        
        vbox.append(grid)
        page.set_child(vbox)
        
        self.add_page(page,"general","Generic settings")
    
    def _on_backupdir_dialog_select_folder(self,dialog,result,*data):
        try:
            dir = dialog.select_folder_finish(result)
            if dir is not None:
                self.__backupdir_label.set_text(dir.get_path())
        except:
            pass
        
    def _on_backupdir_button_clicked(self,button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("sgbackup: Choose backup folder")
        dialog.select_folder(self,None,self._on_backupdir_dialog_select_folder)
        
        
        
    def add_page(self,page,name,title):
        self.__stack.add_titled(page,name,title)
        
    def do_response(self,response):
        if response == Gtk.ResponseType.APPLY:
            self.emit('save')
            settings.save()
        self.destroy()
            
    @Signal(name='save')
    def do_save(self):
        settings.backup_dir = self.__backupdir_label.get_text()
        