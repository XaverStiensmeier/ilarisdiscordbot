#!/bin/sh
cd resources/manoeverkarten
for file in * ; do
    mv -v "$file" "${file#*_}"
done
for file in *.pdf ; do
    echo "$file"
    pdftoppm "$file" "${file%????}" -png -singlefile
done
#find . -maxdepth 1 -type f -name '*.pdf' -exec pdftoppm -png {} {} \;