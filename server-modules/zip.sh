#!/bin/sh
for i in `echo \
fts-indexes \
full_text_search \
ktiny \
maps \
jasper_reports \
smart_attach`

do 
echo $i
zip -r $i.zip $i

done

