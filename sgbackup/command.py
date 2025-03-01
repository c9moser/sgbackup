
###############################################################################
# sgbackup - The SaveGame Backup tool                                         #
#    Copyright (C) 2024,2025  Christian Moser                                      #
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


class Command:
    def __init__(self,id:str,name:str,description:str):
        self.__id = id
        self.__name = name
        self.__description = description
        
    def get_name(self):
        return self.__name
    
    def get_id(self):
        return self.__id
    
    def get_description(self):
        return self.__description
    
    def get_help(self):
        raise NotImplementedError("Command.get_help() is not implemented!")
    
    def get_synopsis(self):
        raise NotImplementedError("Command.get_synopsis() is not implemented!")
    
    def execute(self,argv:list):
        raise NotImplementedError("Command.execute is not implemented!")

