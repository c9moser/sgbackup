#!/bin/sh

# (c) 2021,2022 Christian Moser
# LICNENSE: Public Domain
# Version: 0.3.0

PREFIX="/usr/local"
BINDIR="${PREFIX}/bin"
ETCDIR="${PREFIX}/etc"
SHAREDSTATEDIR="${PREFIX}/share/sgbackup"
SCRIPTDIR="${SHAREDSTATEDIR}/scripts"
CONFDIR="${ETCDIR}/sgbackup.config"
SGCONF="${ETCDIR}/sgbackup.conf"
INSTALLROOT="${0%/install.sh}"
WRITE_CONF="YES"

echo -n "Do you want to install sgbackup for all users [y/n]? "
read install

if [ "x$install" = "xn" -o "x$install" = "xN" -o "x$install" = "xno" ] ; then
	PREFIX="$HOME"
	BINDIR="$HOME/bin"
	ETCDIR="${HOME}"
	SHAREDSTATEDIR="${HOME}/.local/share"
	SCRIPTDIR="${HOME}/bin/sgbackup.scripts"
	CONFDIR="${BINDIR}/sgbackup.config"
	SGCONF="${HOME}/.sgbackup.conf"
	WRITE_CONF="NO"
fi

if [ ! -d "${BINDIR}" ]; then
	mkdir -pv "${BINDIR}"
fi

if [ ! -d "${ETCDIR}" ]; then
	mkdir -pv "${ETCDIR}"
fi

if [ ! -d "${SHAREDSTATEDIR}" ]; then
	mkdir -pv "${SHAREDSTATEDIR}"
fi

if [ ! -d "${SCRIPTDIR}" ]; then
	mkdir -pv "${SCRIPTDIR}"
fi

if [ ! -d "${CONFDIR}" ]; then
	mkdir -pv "${CONFDIR}"
fi

if [ -f "${SGCONF}" ]; then
	WRITE_CONF="NO"
fi

cp -v "${INSTALLROOT}/sgbackup" "${BINDIR}/sgbackup"
cp -v "${INSTALLROOT}/sgbackup-mkiso" "${BINDIR}/sgbackup-mkiso"
cp -v "${INSTALLROOT}/sgbackup-ftp" "${BINDIR}/sgbackup-ftp"
cp -v "${INSTALLROOT}/sgbackup-burn-iso" "${BINDIR}/sgbackup-burn-iso"
cp -v "${INSTALLROOT}/README.md" "${SHAREDSTATEDIR}/README.md"
cp -v "${INSTALLROOT}/INSTALL" "${SHAREDSTATEDIR}/INSTALL"
cp -v "${INSTALLROOT}/LICENSE" "${SHREDSTATEDIR}/LICENSE"
cp -v "${INSTALLROOT}/sgbackup.scripts/"* "${SCRIPTDIR}/"

if [ "$WRITE_CONF" = "YES" ]; then
	echo "SG_CONF_DIR=\"${CONFDIR}\"" > "${SGCONF}"
	echo "SG_SCRIPT_DIR=\"${SCRIPTDIR}\"" >> "${SGCONF}"
fi

echo ""
echo -n "Do you want to install \${game}.conf files [y/n/a]? "
read installconf

if [ "x${installconf}" = "xn" -o "x${installconf}" = "xN" -o "x${installconf}" = "xno" ]; then
	exit
elif [ "x${installconf}" = "xa" -o x"${installconf}" = "xA" ]; then
	for i in "${INSTALLROOT}/sgbackup.config"/*.conf; do
		source "$i"
		echo -n "Install config for game \"$NAME\" [y/n]? "
		read instconf
		if [ "x$instconf" = "n" -o "x$instconf" = "N" ];	then
			continue
		else
			cp -v "$i" "${CONFDIR}/"
		fi
	done
else
	cp -v "${INSTALLROOT}/sgbackup.config"/* "${CONFDIR}/"
fi

