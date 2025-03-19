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

import os,sys
from i18n import gettext as _
from string import Template

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

PLATFORM_WINDOWS = bool(sys.platform == 'win32')
PLATFORM_LINUX = _platform_is_linux()
PLATFORM_MACOS = bool(sys.platform == 'darwin')
PLATFORM_UNIX = _platform_is_unix()

del _platform_is_unix
del _platform_is_linux
    
def sanitize_windows_path(path:str)->str:
    return path.replace('/','\\')

def sanitize_path(path:str)->str:
    if (PLATFORM_WINDOWS):
        return sanitize_windows_path(path)
    return path

def create_help_title(self,title:str):
    help=_("HELP")

    if (len(title) + 2) <= (40 - (len(help) / 2)):
        ret = title + (" " * (40 - (len(help) / 2) - len(title))) + help + "\n"
    else:
        ret = title + "  " + help + "\n"

    ret += 80 * "="

    return ret    

def get_help_from_template_string(self,text:str,variables:dict):
    if not 'name' in variables:
        variables['TITLE'] = self.create_help_title(_('sgbackup'))
    else:
        variables['TITLE'] = self.create_help_title(variables['name'])

    template = Template(text)
    return template.safe_substitute(variables)

def get_help_from_template_file(self,filename,variables:dict):
    with open(filename,'r',encoding='utf-8') as ifile:
        return get_help_from_template_string(ifile.read(),variables)
    
def get_builtin_help(topic,variables:dict):
    lang = _('help-lang:en')
    if lang.sstartswith('help-lang:'):
        lang = lang[len('help-lang:')]

    help_dir = os.path.join(os.path.dirname(__file__),'help')
    for i in (os.path.join(help_dir,lang,topic + '.help'), 
              os.path.join(help_dir,'en', topic + '.help')):
        if os.path.isfile(i):
            return get_help_from_template_file(i,variables)
    return ""
