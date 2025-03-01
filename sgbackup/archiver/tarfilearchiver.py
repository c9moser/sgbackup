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

from gi.repository.GObject import Property
from gi.repository import GLib

from ._archiver import Archiver
from tarfile import open as tf_open, is_tarfile
from tempfile import mkdtemp,NamedTemporaryFile
import json
import os
from ..game import Game
import logging
logger = logging.getLogger(__name__)

class TarfileArchiver(Archiver):
    def __init__(self,
                 key='tarfile',
                 name="TarFile",
                 extensions=['.tar'],
                 description="Archiver for .tar files.",
                 compression=None):
        Archiver.__init__(self,key,name,extensions,description)
        if compression is None:
            self.__compression=""
        else:
            self.__compression=compression
            
    @Property
    def compression(self):
        return self.__compression
        
    def is_archive(self, filename):
        if (Archiver.is_archive(self,filename) and is_tarfile(filename)):
            try:
                with tf_open(filename,"r:{}".format(self.compression)) as tf:
                    #return ("gameconf.json" in tf.getnames())
                    return True
            except:
                pass
            return False
            
    def do_backup(self, game, filename):
        _calc_fraction = lambda n,cnt: ((1.0 / n) * cnt)
        
        self._backup_progress(game,0.0,"Starting {game} ...".format(game=game.name))
        files = game.get_backup_files()
        
        n = len(files) + 2
        cnt=1
        data=json.dumps(game.serialize(),ensure_ascii=False,indent=4)
        
        with tf_open(filename,'x:{}'.format(self.compression)) as tf:
            self._backup_progress(game,_calc_fraction(n,cnt),"gameconf.json")
            gcf = os.path.join(GLib.get_tmp_dir(),"sgbackup-" + GLib.get_user_name() + "." + "backup." + game.key + ".gameconf.tmp")
            with open(gcf,"wt",encoding="utf-8") as gcfile:
                gcfile.write(data)
                
            tf.add(gcf,"gameconf.json")
            
            for path,arcname in files.items():
                cnt += 1
                self._backup_progress(game,_calc_fraction(n,cnt),"arcname")
                tf.add(path,arcname)
                
        self._backup_progress(game,1.0,message="Finished ...")
        return True
    
    def do_restore(self,filename):
        def rmdir_recursive(dir):
            for dirent in os.listdir(dir):
                fname = os.path.join(dirent)
                
                if os.path.islink(fname):
                    os.unlink(fname)
                elif os.path.isdir(fname):
                    rmdir_recursive(fname)
                else:
                    os.unlink(fname)
            os.rmdir(dir)
            
        if not self.is_archive(filename):
            raise RuntimeError("{file} is not a vaild {archiver} archive!".format(file=filename,archiver=self.name))
        
        tempdir = mkdtemp(suffix="-sgbackup")
        tempfile= os.path.join(tempdir,"gameconf.json")
        try:
            with tf_open(filename,'r:{}'.format(self.compression)) as tf:
                tf.extract("gameconf.json",tempdir)
                with open(tempfile,"r",encoding="utf-8") as ifile:
                    game = Game.new_from_json_file(tempfile)
                    if not os.path.isdir(game.savegame_root):
                        os.makedirs(game.savegame_root)
                    
                    for arcname in [i for i in tf.getnames() if i not in ("gameconf.json",'.','..')]:
                        tf.extract(arcname,path=game.savegame_root)
                        
                rmdir_recursive(tempdir)
                return True
        except Exception as ex:
            logger.error("Restoring archive {file} failed! ({message})".format(
                file=filename,
                message=str(ex)))
        
        if os.path.isdir(tempdir):
            rmdir_recursive(tempdir)
            
        return False
        
        
class TarfileBz2Archiver(TarfileArchiver):
    def __init__(self):
        TarfileArchiver.__init__(self,
                                 'tarfile-bz2',
                                 "TarfileBzip2",
                                 ['.tbz','.tar.bz2','tar.bzip2'],
                                 "Archiver for bzip2 compressedd tar archives.",
                                 "bz2")
        
class TarfileGzArchiver(TarfileArchiver):
    def __init__(self):
        TarfileArchiver.__init__(self,
                                 'tarfile-gz',
                                 "TarfileGzip",
                                 ['.tgz','.tar.gz'],
                                 "Archiver for gzip compressed tar archives.",
                                 "gz")
        
class TarfileXzArchiver(TarfileArchiver):
    def __init__(self):
        TarfileArchiver.__init__(self,
                                 'tarfile-xz',
                                 "TarfileXz",
                                 ['.txz','.tar.xz'],
                                 "Archiver for xz compressed tar archives.",
                                 'xz')
        
ARCHIVERS=[
    TarfileArchiver(),
    TarfileBz2Archiver(),
    TarfileGzArchiver(),
    TarfileXzArchiver(),
]
