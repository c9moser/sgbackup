#!/bin/sh
self="$( realpath "$0" )"
scriptdir="$( dirname "$self" )"
project_root="$( dirname "$( dirname "$self" )" )"

PO_DIR="${project_root}/PO"

cd "$prject_root"
sources="${PO_DIR}/SOURCES"
ui_sources="${PO_DIR}/UI.SOURCES"
pot_file="${PO_DIR}/messages.pot"

[ -f "$sources" ] && rm "$sources"
[ -f "$ui_sources" ] && rm "$ui_sources"

for i in $( find "./sgbackup" | egrep '\.py$' ); do
    echo "${i#./}" >> "$sources"
done
for i in $( find "./sgbackup" | egrep '\.ui$' ); do
    echo "${i#./}" >> "$ui_sources"
done

/usr/bin/xgettext -o "$pot_file" --force-po -l Python -c -k_ -kN_ -kQ_ -f "$sources" --color=auto -n --copyright-holder="sgbackup Team" --package-name="sgbackup"
/usr/bin/xgettext -o "$pot_file" -l Glade -j -f "$ui_sources" --color=auto -n
