#!/bin/sh
cd resources/manoeverkarten || return
for file in * ; do
    mv -v "$file" "${file#*_}"
done
for file in *.pdf ; do
    echo "$file"
    pdftoppm "$file" "${file%????}" -png -singlefile
done
rm ./*glob*.pdf