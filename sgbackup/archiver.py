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

from gi.repository.GObject import (
    GObject,
    Property,
    Signal,
    SignalFlags,
    signal_accumulator_true_handled,
)

from .game import Game

class Archiver:
    def __init__(self,key:str,name:str,extensions:list[str],decription:str|None=None):
        self.__key = key
        self.__name = name
        if decription:
            self.__description = decription
        else:
            self.__description = ""
            
    @Property(type=str)
    def name(self)->str:
        return self.__name
    
    @Property
    def key(self)->str:
        return self.__key
    
    @Property
    def description(self)->str:
        return self.__description
    
    def backup(self,game)->bool:
        pass
    
    def restore(self,game,file)->bool:
        pass
    
    @Signal(name="backup",flags=SignalFlags.RUN_FIRST,
            return_type=bool, arg_types=(GObject,str),
            accumulator=signal_accumulator_true_handled)
    def do_backup(self,game:Game,filename:str):
        pass
    
    @Signal(name="restore",flags=SignalFlags.RUN_FIRST,
            return_type=bool,arg_types=(GObject,str),
            accumulator=signal_accumulator_true_handled)
    def do_backup(self,game:Game,filanme:str):
        pass