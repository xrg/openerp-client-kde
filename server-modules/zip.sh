#!/bin/sh
for i in `echo \
fts-indexes \
full_text_search \
ktiny \
maps \
smart_attach`

do 
echo $i
zip -r $i.zip $i

done

