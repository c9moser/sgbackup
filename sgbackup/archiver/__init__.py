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

from ._archiver import Archiver,ArchiverManager
#import importlib
import os

_archiver = ArchiverManager.get_global()
_archiver_path= os.path.dirname(__file__)
for dirent in os.listdir(_archiver_path):
    if dirent.startswith('.') or dirent.startswith('_'):
        continue
    if dirent.endswith('.py'):
        module = dirent[0:-3]
        exec("""
from . import {module}
if hasattr({module},"ARCHIVERS"):
    for a in {module}.ARCHIVERS:
        _archiver.archivers[a.key] = a
""".format(module=module))

__ALL__ = [
    "Archiver",
    "AchiverManager",
    "archiver",
]
