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

from ._archiver import Archiver
import zipfile
import json
import os
from ..game import Game,GameManager
from ..settings import settings

class ZipfileArchiver(Archiver):
    def __init__(self):
        Archiver.__init__(self,"zipfile","ZipFile",[".zip"],"Archiver for .zip files.")
        
    def do_backup(self, game:Game, filename:str):
        _calc_fraction = lambda n,cnt: ((1.0 / n) * cnt)
        
        self._backup_progress(game,0.0,"Starting {game} ...".format(game=game.name))
        
        files = game.get_backup_files()
        div = len(files) + 2
        cnt=1
        game_data = json.dumps(game.serialize(),ensure_ascii=False,indent=4)
        with zipfile.ZipFile(filename,mode="w",
                             compression=settings.zipfile_compression,
                             compresslevel=settings.zipfile_compresslevel) as zf:
            self._backup_progress(game,_calc_fraction(div,cnt),"{} -> {}".format(game.name,"gameconf.json"))
            zf.writestr("gameconf.json",game_data)
            for path,arcname in files.items():
                cnt+=1
                self._backup_progress(game,_calc_fraction(div,cnt),"{} -> {}".format(game.name,arcname))
                zf.write(path,arcname)
                
        self._backup_progress(game,1.0,"{game} ... FINISHED".format(game=game.name))
        
                
    def is_archive(self,filename:str)->bool:
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename,"r") as zf:
                if 'gameconf.json' in [i.filename for i in zf.filelist]:
                    return True
        return False
    
    def do_restore(self,filename:str):
        # TODO: convert savegame dir if not the same SvaegameType!!!
        
        if not zipfile.is_zipfile(filename):
            raise RuntimeError("\"{filename}\" is not a valid sgbackup zipfile archive!")
        
        with zipfile.ZipFile(filename,"r") as zf:
            zip_game = Game.new_from_dict(json.loads(zf.read('game.conf').decode("utf-8")))
            try:
                game = GameManager.get_global().games[zip_game.key]
            except:
                game = zip_game
                
            if not os.path.isdir(game.savegame_root):
                os.makedirs(game.savegame_root)
                
            extract_files = [i for i in zf.filelist if i.startswith(zip_game.savegame_dir + "/")]
            for file in extract_files:
                zf.extract(file,game.savegame_root)
                
        return True

ARCHIVERS = [
    ZipfileArchiver(),
]