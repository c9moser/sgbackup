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
from gi.repository.GObject import GObject,Property

from ..version import VERSION
from ..i18n import gettext as _



class AboutDialog(Gtk.AboutDialog):
    def __init__(self):
        Gtk.AboutDialog.__init__(self)
        self.set_program_name("SGBackup")
        self.set_version(VERSION)
        self.set_logo_icon_name("sgbackup-symbolic")
        self.set_website("https://github.com/c9moser/sgbackup")
        self.set_copyright("(C) 2024,2025 Christian Moser")
        self.set_license_type(Gtk.License.GPL_3_0)
        self.set_authors([
            "Christian Moser <christian@mydevel.at>"
        ])

class NoGamesToBackupDialog(Gtk.MessageDialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.MessageDialog.__init__(self,
                                   message=_("There are no games to backup!"),
                                   use_markup=False,
                                   buttons=Gtk.ButtonsType.OK)
        
        if parent:
            self.set_transient_for(parent)
        self.set_modal(True)
        
    def do_response(self,response):
        self.hide()
        self.destroy()
        
class NoGamesToBackupFoundDialog(Gtk.MessageDialog):
    def __init__(self,parent:Gtk.Window|None=None):
        Gtk.MessageDialog.__init__(self,
                                   message=_("There were no games to backup found!"),
                                   buttons=Gtk.ButtonsType.OK)
        
        if parent:
            self.set_transient_for(parent)    
        self.set_modal(True)
        
    def do_response(self,response):
        self.hide()
        self.destroy()
        

