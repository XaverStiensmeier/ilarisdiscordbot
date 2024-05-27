#!/bin/sh
cd ../resources/manoeverkarten || return
for file in *.pdf ; do
    echo "$file"
    pdftoppm "$file" "${file%????}" -png -singlefile
done
rm *.pdf