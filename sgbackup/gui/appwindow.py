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

from gi.repository import Gtk,Gio,GObject

import os
from .gameview import GameView
from .backupview import BackupView

class AppWindow(Gtk.ApplicationWindow):
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
        
    @GObject.Property
    def builder(self):
        return self.__builder

    @GObject.Property
    def backupview(self):
        return self.__backupview
    
    @GObject.Property
    def gameview(self):
        return self.__gameview
    
        