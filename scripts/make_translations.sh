#!/bin/sh
self="$( realpath "$0" )"
scriptdir="$( dirname "$self" )"
project_root="$( dirname "$( dirname "$self" )" )"

PO_DIR="${project_root}/PO"
LINGUAS="${PO_DIR}/LINGUAS"
LOCALEDIR="${project_root}/sgbackup/locale"

for i in $( cat "$LINGUAS" );do
    po="${PO_DIR}/${i}.po"

    [ ! -f "$po" ] && continue

    msgdir="${LOCALEDIR}/${i}/LC_MESSAGES"
    mo="${msgdir}/sgbackup.mo"

    [ ! -d $msgdir ] && mkdir -pv "$msgdir"

    msgfmt -o "$mo" "$po"
done
