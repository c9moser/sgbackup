#!/bin/sh
self="$( realpath "$0" )"
scriptdir="$( dirname "$0" )"
project_root="$( dirname "$(dirname "$self" )" )"

PO_DIR="${project_root}/PO"
LINGUAS="${PO_DIR}/LINGUAS"

pot_file="${PO_DIR}/messages.pot"

for i in $( cat "$LINGUAS" ); do
    po="${PO_DIR}/${i}.po"
    if [ ! -f "$po" ]; then
        cp "$pot_file" "$po"
    else
        msgmerge --update --previous --lang="$i" "$po" "$pot_file"
    fi
done
