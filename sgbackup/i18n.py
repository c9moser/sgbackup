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

from os.path import dirname,join
import gettext as _gettext

TEXTDOMAIN="sgbackup"

_gettext.bindtextdomain(TEXTDOMAIN,join(dirname(__file__),'locale'))

gettext = lambda s: _gettext.dgettext(TEXTDOMAIN,s)
pgettext = lambda context,s: _gettext.dpgettext(TEXTDOMAIN,context,s)
ngettext = lambda singular,plural,n: _gettext.dngettext(TEXTDOMAIN,singular,plural,n)
npgettext = lambda context,singular,plural,n: _gettext.dnpgettext(TEXTDOMAIN,context,singular,plural,n)
noop = lambda s: s
