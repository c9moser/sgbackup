#!/bin/bash
# vim: ts=4 sts=4 sw=4 smartindent expandtab autoindent ff=unix

SELF="$(realpath "$0")"
PROJECT_ROOT="$(dirname "$SELF")"
: ${PYTHON_VENV_DIR:=${HOME}/.local/venv}

if [ "$INSTALL_REQUIREMENTS" = "yes" ]; then
    "${PROJECT_ROOT}/centos-install-requirements.sh"
fi

if [ ! -d "$PYTHON_VENV_DIR" ]; then
    mkdir -pv "$PYTHON_VENV_DIR"
fi

python -m venv --system-site-packages "${PYTHON_VENV_DIR}/sgbackup"
. "${PYTHON_VENV_DIR}/sgbackup/bin/activate"
pip install --upgrade pip
pip install -r "${PROJECT_ROOT}/requirements.txt"
make -C "${PROJECT_ROOT}" translations
pip install "${PROJECT_ROOT}"

if [ ! -d ~/.local/bin ]; then
    mkdir -pv ~/.local/bin
fi

cat > "${PYTHON_VENV_DIR}/sgbackup/bin/sgbackup" << EOF
#!/bin/bash

SELF="\$(realpath "\$0")"
echo \$SELF
VENV_BINDIR="\$(dirname "\$SELF")"
echo \$VENV_BINDIR
. "\$VENV_BINDIR/activate"

echo "\$@"
python -m sgbackup "\$@"
exit_code=\$?

deactivate
exit \$exit_code
EOF
chmod +x "${PYTHON_VENV_DIR}/sgbackup/bin/sgbackup"
ln -sv "${PYTHON_VENV_DIR}/sgbackup/bin/sgbackup" ~/.local/bin/sgbackup

cat > "${PYTHON_VENV_DIR}/sgbackup/bin/gsgbackup" << EOF
#!/bin/bash

SELF="\$(realpath "\$0")"
VENV_BINDIR="\$(dirname "\$SELF")"

. "\$VENV_BINDIR/activate"

python -m sgbackup.gui "\$@"
exit_code=\$?

deactivate
exit \$exit_code
EOF
chmod +x "${PYTHON_VENV_DIR}/sgbackup/bin/gsgbackup"
ln -sv "${PYTHON_VENV_DIR}/sgbackup/bin/gsgbackup" ~/.local/bin/gsgbackup

