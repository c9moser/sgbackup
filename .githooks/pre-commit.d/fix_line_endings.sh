#!/usr/bin/env bash
# vim: syn=sh ts=4 sts=4 sw=4 smartindent expandtab ff=unix

dos2unix=$(which dos2unix)
unix2dos=$(which unix2dos)

githooks="pre-commit prepare-commit-msg commit-msg post-commit applypatch-msg pre-applypatch post-applypatch pre-rebase post-rewrite post-checkout post-merge"

dos2unix_used=NO

__IFS="$IFS"
IFS=$'\n'
if [ -n "$dos2unix" -a "$unix2dos" ]; then
	for line in $(git status -s); do
        if [[ line == A* || $line == M* ]]; then
            file="${line:3}"
            abspath="${PROJECT_ROOT}/$file"

            if [[ $file == *.py || $file == *.sh || file == *.rst ]]; then
                $dos2unix "$abspath"
                git add "$file"
                dos2unix_used=YES
                continue
            fi

            #check if we are updating a githook
            for githook in $githooks; do
                if [ "$file" = ".githooks/$githook" ]; then
                    $dos2unix "$abspath"
                    git add "$file"
                    dos2unix_used=YES
                    break
                fi
            done
        fi

        if [ "$dos2unix_used" = "YES" ]; then
            continue
        fi
        if [[ "$file" == *.txt ]]; then
            $unix2dos "$abspath"
            git add "$file"
        fi
    done
else
    echo "\"dos2unix\" and/or \"unix2dos\" not found!" >&2
fi
IFS="$__IFS"
