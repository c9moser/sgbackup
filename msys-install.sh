#!/bin/bash
# vim: syn=sh ts=4 sts=4 sw=4 smartindent expandtab ff=unix

SELF="$( realpath "$0" )"
PROJECT_DIR="$( dirname "$SELF")"

PACKAGES="gtk4 gobject-introspection python-gobject python-rapidfuzz"

_install_pkg=""
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

cat > "${bindir}/sgbackup.bat" << EOF
@ECHO OFF\r
"$pythonpath" -m sgbackup %*\r
EOF

cat > "${bindir}/gsgbackup" << EOF
#!/bin/bash

python -m sgbackup.gui "\$@"
EOF

cat > "${bindir}/gsgbackup.bat" << EOF
@ECHO OFF\r
"$pythonpath" -m sgbackup.gui %*
EOF

