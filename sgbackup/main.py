#enconding: utf-8
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

import logging
from . import gui
from .gui.application import Application
from .steam import SteamLibrary
import sys

logger=logging.getLogger(__name__)


def cli_main():
    logger.debug("Running cli_main()")
    return 0

def curses_main():
    logger.debug("Running curses_main()")
    return 0


def gui_main():
    logger.debug("Running gui_main()")
    gui.app = Application()
    gui.app.run()
    return 0