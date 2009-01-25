rmdir dist /s /q
rmdir build /s /q
setup.py py2exe
cd nsis
"%PROGRAMFILES%"\NSIS\makensisw.exe koo-installer.nsi
cd ..

