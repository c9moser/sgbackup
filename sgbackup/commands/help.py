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

import os,sys
from sgbackup import __version__ as VERSION
from ..settings import settings
from ..command import Command
from .. import commands
from gi.repository import GLib
from io import StringIO
from subprocess import run

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
                print(commands.COMMANDS[i].get_synopsis())
            except:
                self.logger.error("No such command {command}".foramt(command=i))
                error_code = 4
        
        return error_code
    

class HelpCommand(Command):
    def __init__(self):
        super().__init__('help','Help', 'Show help for commands.')
        
    def get_synopsis(self):
        return "sgbackup help [COMMAND]"
    
    def get_sgbackup_help(self):
        return commands.COMMANDS['synopsis'].get_sgbackup_synopsis()
    
    def get_help(self):
        return self.get_synopsis()
    
    def execute(self,argv):
        if (len(argv) < 1):
            message = self.get_sgbackup_help()
        else:
            try:
                message = commands.COMMANDS[argv[0]].get_help()
            except:
                logger.error("No such command \"{}\"!".format(argv[0]))
                return 2
            
        if (sys.stdout.isatty() and settings.cli_pager is not None):
            r,w = os.pipe()
            with os.fdopen(w,'w',encoding="utf-8") as wr_stdin:
                wr_stdin.write(message)
                
            with os.fdopen(r,'r') as rd_stdin:
                proc = run([settings.cli_pager],stdin=rd_stdin,shell=True,encoding="utf-8")
            return proc.returncode
        
        print(message)
        
        return 0

__synopsis = SynopsisCommand()

COMMANDS = {
    'version':VersionCommand(),
    'synopsis': __synopsis,
    'usage': __synopsis,
    'help': HelpCommand(),
}
