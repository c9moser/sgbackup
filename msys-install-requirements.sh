#!/bin/bash
# vim: syn=sh ts=4 sts=4 sw=4 smartindent expandtab ff=unix

PACKAGES="gtk4 gobject-introspection python-gobject python-rapidfuzz"

_install_pkg=""
for i in $PACKAGES; do
	_install_pkg="${_install_pkg} ${MINGW_PACKAGE_PREFIX}-$i"
done

pacman -Sy
pacman -S --noconfirm $_install_pkg

