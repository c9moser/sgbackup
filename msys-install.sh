#!/bin/bash
# vim: syn=sh ts=4 sts=4 sw=4 smartindent expandtab ff=unix

SELF="$( realpath "$0" )"
PROJECT_DIR="$( dirname "$SELF")"
: ${PYTHON_VENV_DIR:=$(cygpath "$USERPROFILE")/python-venv}
venv="${PYTHON_VENV_DIR}/sgbackup"
venv_bin="${venv}/bin"
wvenv_bin="$(cygpath -w "$venv_bin")"

PACKAGES="gtk4 gobject-introspection python-pip python-gobject python-rapidfuzz"

_install_pkg="base-devel"
for i in $PACKAGES; do
	_install_pkg="${_install_pkg} ${MINGW_PACKAGE_PREFIX}-$i"
done

pacman -Sy
pacman -S --noconfirm $_install_pkg

if [ ! -f "$venv/bin/activate" ]; then
    python -m venv --system-site-packages "$venv"
fi

. "$venv/bin/activate"
if [ $? -ne 0 ]; then
    exit "Unable to load venv"
fi

cd $PROJECT_DIR

# translations
make translations
MSYS_LOCALEDIR="${MSYSTEM_PREFIX}/share/locale"
for i in  $( cat "$PROJECT_DIR/PO/LINGUAS" ); do
    mo="${PROJECT_DIR}/sgbackup/locale/${i}/LC_MESSAGES/sgbackup.mo"
    localedir="${MSYS_LOCALEDIR}/${i}/LC_MESSAGES"

    [ ! -d "$localedir" ] && mkdir -p "$localedir"
    cp -v "$mo" "$localedir"
done

# install
pip install --verbose --user .

bindir=$( realpath "$venv/bin" )
wbindir=$( cygpath -w "$bindir" )

pythonpath="$( python -c 'import sys; print(sys.executable.replace("/","\\"))' )"
pythonwpath="$( pythonw -c 'import sys; print(sys.executable.replace("/","\\"))' )"
cat > "${venv_bin}/sgbackup" << EOF
#!/bin/bash

. "$venv_bin/activate"

python -m sgbackup "\$@"
EOF

cat > "${venv_bin}/sgbackup.cmd" << EOF
@ECHO OFF
powershell -File "$wvenv_bin\\sgbackup.ps1" %*
EOF
unix2dos "${venv_bin}/sgbackup.cmd"

cat > "${venv_bin}/sgbackup.ps1" << EOF
Set-ExecutionPolicy Unrestricted -Scope Process -Force

$wvenv_bin\\activate.ps1

$pythonpath -m sgbackup $args
EOF
unix2dos "$venv_bin/sgbackup.ps1"

cat > "${venv_bin}/gsgbackup.ps1" << EOF
$wvenv_bin\\activate.ps1
$pythonpath -m sgbackup.gui $args
EOF
unix2dos "$venv_bin/gsgbackup.ps1"

cat > "${venv_bin}/gsgbackup" << EOF
#!/bin/bash

python -m sgbackup.gui "\$@"
EOF

cat > "${venv_bin}/gsgbackup.cmd" << EOF
@ECHO OFF
powershell -File "$wvenv_bin\\gsgbackup.ps1" %*
EOF
unix2dos "${bindir}/gsgbackup.cmd"

install_ps1="${PRJECT_DIR}/install.ps1"
wproject_dir="$( cygpath -w "${PROJECT_DIR}" )"

cat > "$install_ps1" << EOF
[Environment]::SetEnvironmentVariable("Path","\$env:PATH;$wbindir","User")

\$desktop_dir=[Environment]::getFolderPath("Desktop")
\$startmenu_dir=[Environment]::getFolderPath("StartMenu") + "\\Programs"
\$picture_dir=[Environment]::getFolderPath("MyPictures")

Copy-Item -Path "$wproject_dir\\sgbackup\\icons\\sgbackup.ico" -Destination "\$picture_dir\\sgbackup.ico" -Force

foreach (\$dir in \$desktop_dir,\$startmenu_dir) {
    \$shell=New-Object -ComObject WScript.Shell
    \$shortcut=\$shell.CreateShortcut("\$dir\\sgbackup.lnk")
    \$shortcut.TargetPath='powershell'
    \$shortcut.Arguments='-WindowStyle hidden -File "$wvenv_bin\\gsgbackup.ps1"'
    \$shortcut.IconLocation="\$picture_dir\\sgbackup.ico"
    \$shortcut.Save()
}
EOF
unix2dos "$install_ps1"
powershell -File "$( cygpath -w "$install_ps1" )"
rm "$install_ps1"

