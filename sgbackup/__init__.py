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

from . import _import_gtk
from .version VERSION
__version__ = VERSION
from .settings import settings
from . import _logging
from .main import cli_main,gui_main
from . import game
from .command import Command
from . import commands
from . import archiver

__ALL__ = [
    "settings"
    "cli_main",
    "gui_main",
    #"curses_main",
    'game',
    "Command",
    "commands",
    "archiver",
]
