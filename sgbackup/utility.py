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

import sys
def _platform_is_linux():
    if sys.platform == 'linux':
        return True
    for i in ('freebsd','netbsd','openbsd','dragonfly'):
        if sys.platform.startswith(i):
            return True
    return False

def _platform_is_unix():
    if sys.platform in ('linux','darwin','aix'):
        return True
    for i in ('freebsd','netbsd','openbsd','dragonfly'):
        if sys.platform.startswith(i):
            return True
    return False

PLATFORM_WINDOWS = (sys.platform == 'win32')
PLATFORM_LINUX = _platform_is_linux()
PLATFORM_MACOS = (sys.platform == 'darwin')
PLATFORM_UNIX = _platform_is_unix()

del _platform_is_unix
del _platform_is_linux
    
def sanitize_windows_path(path:str)->str:
    return path.replace('/','\\')

def sanitize_path(path:str)->str:
    if (PLATFORM_WINDOWS):
        return sanitize_windows_path(path)
    return path
