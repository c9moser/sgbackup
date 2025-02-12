#!/bin/bash
# vim: syn=sh ts=4 sts=4 sw=4 smartindent expandtab ff=unix

SELF="$( realpath "$0" )"
PROJECT_DIR="$( dirname "$SELF")"

PACKAGES="gtk4 gobject-introspection python-gobject python-rapidfuzz"

_install_pkg="base-devel"
for i in $PACKAGES; do
	_install_pkg="${_install_pkg} ${MINGW_PACKAGE_PREFIX}-$i"
done

pacman -Sy
pacman -S --noconfirm $_install_pkg

cd $PROJECT_DIR
pip install --user .

bindir=$( realpath ~/bin )
wbindir=$( cygpath -w "$bindir" )
if [ ! -d "$bindir" ]; then
    mkdir -p "$bindir"
fi

pythonpath="$( python -c 'import sys; print(sys.executable)' )" 
cat > "${bindir}/sgbackup" << EOF
#!/bin/bash

python -m sgbackup "\$@"
EOF

cat > "${bindir}/sgbackup.cmd" << EOF
@ECHO OFF
"$pythonpath" -m sgbackup %*
EOF
unix2dos "${bindir}/sgbackup.cmd"

cat > "${bindir}/gsgbackup" << EOF
#!/bin/bash

python -m sgbackup.gui "\$@"
EOF

cat > "${bindir}/gsgbackup.cmd" << EOF
@ECHO OFF
"$pythonpath" -m sgbackup.gui %*
EOF
unix2dos "${bindir}/gsgbackup.cmd"

install_ps1="${PRJECT_DIR}/install.ps1"
wproject_dir="$( cygpath -w "${PROJECT_DIR}" )"

cat > "$install_ps1" << EOF
[Environment]::SetEnvironemtnVariable("Path","\$env:PATH;$wbindir","User")

\$desktop_dir=[Environment]::getFolderPath("Desktop")
\$startmenu_dir=[Environment]::getFolderPath("StartMenu")
\$picture_dir=[Environment]::getFolderPath("MyPictures")

Copy-Item -Path "$wproject_dir\\sgbackup\\icons\\sgbackup.ico" -Destination "\$picture_dir\\sgbackup.ico" -Force

foreach (\$dir in \$desktop_dir,\$startmenu_dir) {
    \$shell=New-Object -ComObject WScript.Shell
    \$shortcut=\$shell.CreateShortcut('\$dir\\sgbackup.lnk')
    \$shortcut.TargetPath='$wbindir\\gsgbackup.cmd'
    \$shortcut.IconLocation="\$picture_dir\\sgbackup.ico"
    \$shortcut.Save()
}
EOF
unix2dos "$install_ps1"
powershell -File "$( cygpath -w "$install_ps1" )"
rm "$install_ps1"

