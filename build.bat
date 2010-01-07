rmdir dist /s /q
rmdir build /s /q
c:\python26\python setup.py py2exe
mkdir dist\imageformats
copy c:\python26\lib\site-packages\PyQt4\plugins\imageformats\qjpeg4.dll dist\imageformats\
cd nsis
"%PROGRAMFILES%"\NSIS\makensisw.exe koo-installer.nsi
cd ..

