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

import sys
if sys.platform.lower() == 'win32':
    PLATFORM_WINDOWS=True
else:
    PLATFORM_WINDOWS=False
    
if sys.platform.lower() in ['linux','freebsd','netbsd','openbsd','dragonfly','macos','cygwin']:
    PLATFORM_UNIX = True
else:
    PLATFORM_UNIX = False
    
def sanitize_windows_path(path:str)->str:
    return path.replace('/','\\')

def sanitize_path(path:str)->str:
    if (PLATFORM_WINDOWS):
        return sanitize_windows_path(path)
    return path
