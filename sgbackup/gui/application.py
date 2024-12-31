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

from gi.repository import Gtk,GObject,Gio
from .appwindow import AppWindow

import logging; logger=logging.getLogger(__name__)

class Application(Gtk.Application):
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
    
    @GObject.Property
    def appwindow(self):
        return self.__appwindow
    
    def do_startup(self):
        self._logger.debug('do_startup()')
        if not self.__builder:
            self.__builder = Gtk.Builder.new()
        
        Gtk.Application.do_startup(self)
        
        action_about = Gio.SimpleAction.new('about',None)
        action_about.connect('activate',self.on_action_about)
        self.add_action(action_about)
        
        action_quit = Gio.SimpleAction.new('quit',None)
        action_quit.connect('activate',self.on_action_quit)
        self.add_action(action_quit)
                
        action_settings = Gio.SimpleAction.new('settings',None)
        action_settings.connect('activate',self.on_action_settings)
        self.add_action(action_settings)
        
        # add accels
        self.set_accels_for_action('app.quit',["<Primary>q"])
        
    @GObject.Property
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
        pass
    
    def on_action_quit(self,action,param):
        self.quit()