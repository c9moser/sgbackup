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

import os

COMMANDS = {}

_mods = ['commandbase']

for _f in os.listdir(os.path.dirname(__file__)):
    if _f.startswith('_'):
        continue
    
    if _f.endswith('.py') or _f.endswith('.pyc'):
        if (_f.endswith('py')):
            _m = _f[0:-3]
        else:
            _m = _f[0:-4]

        if _m not in _mods:
            exec("\n".join([
                "from . import " + _m,
                "_mods += _m",
                "_mod = " + _m]))
            if hasattr(_mod,"COMMANDS") and len(_mod.COMMANDS) > 0:
                for _cmd in _mod.COMMANDS:
                    COMMANDS[_cmd.get_id()] = _cmd
                del _cmd
                    
del _mods
del _f
del _m
del _mod
