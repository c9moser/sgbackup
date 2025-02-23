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
from .gui import Application
from .steam import SteamLibrary
import sys
from . import commands

logger=logging.getLogger(__name__)

def cli_main():
    logger.debug("Running cli_main()")
    argc = len(sys.argv)
    if argc < 2:
        return commands.COMMANDS['synopsis'].execute([])
    
    commands_to_execute = []
    last = 0
    command = None
    
    for i in range(1,len(sys.argv)):
        if (sys.argv[i] == '--'):
            if command is not None:
                commands_to_execute.append((command,sys.argv[last+1:i] if last < i else []))
                command = None
            continue
        if command is None:
            try:
                command = commands.COMMANDS[sys.argv[i]]
                last = i
            except:
                logger.error("No such command \"{command}\"!".format(command=sys.argv[i]))
                return 4
            
    if command is not None:
        commands_to_execute.append((command,sys.argv[last+1:] if (last+1) < len(sys.argv) else []))
        command=None
    elif not commands_to_execute:
        return commands.COMMANDS['synopsis'].execute([])
    
    for cmd,argv in commands_to_execute:
        ec = cmd.execute(argv)
        if ec:
            logger.error('sgbackup aborted due to an error!')
            return ec
            
    return 0

def gui_main():
    logger.debug("Running gui_main()")
    gui._app = Application()
    gui._app.run()
    return 0
