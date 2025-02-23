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

from sgbackup import __version__ as VERSION
from ..command import Command

import logging
logger = logging.getLogger(__name__)
class VersionCommand(Command):
    def __init__(self):
        super().__init__('version', 'Version', 'Show version information.')
        
    def get_synopsis(self):
        return 'sgbackup version'
    
    def get_help(self):
        return super().get_help()
    
    def execute(self, argv):
        print("sgbackup - {}".format(VERSION))
        return 0
# VersionCommand class    

class SynopsisCommand(Command):
    def __init__(self):
        super().__init__('synopsis','Synopsis', 'Show usage information.')
        self.logger = logger.getChild('SynopsisCommand')
        
    def get_synopsis(self):
        return "sgbackup synopsis [COMMAND] ..."
    
    def get_sgbackup_synopsis(self):
        return "sgbackup COMMAND1 [OPTIONS1] [-- COMMAND2 [OPTIONS2]] ..."
    
    def get_help(self):
        return super().get_help()
    
    def execute(self,argv):
        error_code = 0
        if not argv:
            print(self.get_sgbackup_synopsis())
            
        for i in argv:
            try:
                print(COMMANDS[i].get_synopsis())
            except:
                self.logger.error("No such command {command}".foramt(command=i))
                error_code = 4
        
        return error_code
    

__synopsis = SynopsisCommand()
            
COMMANDS = {
    'version':VersionCommand(),
    'synopsis': __synopsis,
    'usage': __synopsis
}
