##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#               Based on example script written by Jost Verburg
#               and OpenERP NSIS script by Tiny.be
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################

; In order to compile this installer you'll need:
; a) koo installer (.exe): created with setup.py bdist_wininst
; b) python installer (.msi): download latest from python website
; c) python win32 extensions (.exe): download latest form pywin32 website
; d) pyqt installer (.exe): download latest from pyqt website
; All these files should be placed in the 'nsis' directory. If versions
; have changed you might need to modify 'SecKoo' with the
; appropiate filenames.
;
; Once compiled you should get a file called 'koo-setup.exe' in the 'nsis' 
; directory.
;
; Enjoy!
!ifndef VERSION
    !error "Do not forget to specify Koo's version - /DVERSION=<VERSION>"
!endif 

;--------------------------------
;Include Modern UI

  !include "MUI.nsh"

;--------------------------------
;General

  ;Name and file
  Name "Koo"
  OutFile "koo-setup-${VERSION}.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\Koo"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\Koo" ""

  ;Vista redirects $SMPROGRAMS to all users without this
  RequestExecutionLevel admin
  
  BrandingText "Koo ${VERSION}"

;--------------------------------
;Variables

  Var MUI_TEMP
  Var STARTMENU_FOLDER

  

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING
  
;--------------------------------
;Pages

  !define MUI_ICON "koo.ico"
  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "..\doc\LICENCE.txt"
 # !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Koo"
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Koo"
  
  !insertmacro MUI_PAGE_STARTMENU Application $STARTMENU_FOLDER
  
  !insertmacro MUI_PAGE_INSTFILES

  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_CHECKED
  !define MUI_FINISHPAGE_RUN_TEXT "Start Koo"
  !define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
  ;!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
  ;!define MUI_FINISHPAGE_SHOWREADME $INSTDIR\README.txt
  !insertmacro MUI_PAGE_FINISH

  
  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  !insertmacro MUI_LANGUAGE "Catalan"
  !insertmacro MUI_LANGUAGE "Spanish"
  !insertmacro MUI_LANGUAGE "Italian"

;--------------------------------
;Installer Sections
Function .onInit
    IfSilent AfterLanguageSelection SelectLanguage
    SelectLanguage:
        Push ""
        Push ${LANG_ENGLISH}
        Push English
        Push ${LANG_CATALAN}
        Push "Catalan"
        Push ${LANG_SPANISH}
        Push "Spanish"
	Push ${LANG_ITALIAN}
	Push "Italiano"
        Push A ; A means auto count languages
        ; for the auto count to work the first empty push (Push "") must remain
        LangDLL::LangDialog "$(SelectLanguageTitleText)"  "$(SelectLanguageText)"
        Pop $LANGUAGE
        StrCmp $LANGUAGE "cancel" 0 +2
            Abort
    AfterLanguageSelection:
	ClearErrors
	ReadRegStr $0 HKLM "Software\Koo" ""
	IfErrors DoInstall 0
		MessageBox MB_OK "$(CannotInstallText)"
		Quit
	DoInstall:
	WriteRegStr HKCU "Software\Koo" "Language" $LANGUAGE
	; 1034 - Spanish
	; 1027 - Catalan
	; 1033 - English
FunctionEnd

Section "Koo" SecKoo

    SetOutPath "$TEMP"
    File "vcredist_x86.exe"
    ;ExecWait '"$TEMP\vcredist_x86.exe" /S'
    ExecWait '"$TEMP\vcredist_x86.exe" /q:a /c:"VCREDI~1.EXE /q:a /c:""msiexec /i vcredist.msi /qb!"" "'

    SetOutPath "$INSTDIR"

    File /r "..\dist\*"

    ;Store installation folder
    WriteRegStr HKCU "Software\Koo" "" $INSTDIR
    
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$STARTMENU_FOLDER"
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Koo.lnk" "$INSTDIR\koo.exe"
    CreateShortCut "$DESKTOP\Koo.lnk" "$INSTDIR\koo.exe"

IfSilent RegisterUninstaller NotRegisterUninstaller

RegisterUninstaller:
    ;Create uninstaller
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Koo" "DisplayName" "Koo (remove only)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Koo" "UninstallString" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    Goto ContinueRegister
    
NotRegisterUninstaller:
    WriteRegStr HKLM  "Software\Koo" "UninstallClient" "$INSTDIR\Uninstall.exe"

ContinueRegister:

    WriteUninstaller "$INSTDIR\Uninstall.exe"
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

;Descriptions

;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecKoo} $(DESC_SecKoo)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
 
;--------------------------------
;Uninstaller Section

Section "Uninstall"
  RMDir /r "$INSTDIR"

  !insertmacro MUI_STARTMENU_GETFOLDER Application $MUI_TEMP

  Delete "$SMPROGRAMS\$MUI_TEMP\Koo.lnk"
  Delete "$DESKTOP\Koo.lnk"
  RMDir /r "$SMPROGRAMS\$STARTMENU_FOLDER"

  ;Delete empty start menu parent diretories
  StrCpy $MUI_TEMP "$SMPROGRAMS\$MUI_TEMP"

  startMenuDeleteLoop:
    ClearErrors
    RMDir $MUI_TEMP
    GetFullPathName $MUI_TEMP "$MUI_TEMP\.."

    IfErrors startMenuDeleteLoopDone

    StrCmp $MUI_TEMP $SMPROGRAMS startMenuDeleteLoopDone startMenuDeleteLoop
  startMenuDeleteLoopDone:

  
  DeleteRegKey HKCU "Software\Koo\Language"
  DeleteRegKey HKCU "Software\Koo"
  ;DeleteRegKey /ifempty HKCU "Software\Koo"

  IfSilent RemoveUninstallSingle RemoveUninstallAllInOne
  
  RemoveUninstallSingle:
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Koo"
    goto ContinueUninstall
  
  RemoveUninstallAllInOne:
    DeleteRegKey HKLM "Software\Koo\UninstallClient"

  ContinueUninstall:

SectionEnd

Function LaunchLink
  ExecShell "" "$INSTDIR\koo.exe"
FunctionEnd

;; TRANSLATION STRINGS

;LangString LicenseText ${LANG_ENGLISH} "Usually, a proprietary license is provided with the software: limited number of users, limited in time usage, etc. This Open Source license is the opposite: it garantees you the right to use, copy, study, distribute and modify Open ERP for free."
;LangString LicenseText ${LANG_FRENCH} "Normalement, une licence propri�taire est fournie avec le logiciel: limitation du nombre d'utilisateurs, limitation dans le temps, etc. Cette licence Open Source est l'oppos�: Elle vous garantie le droit d'utiliser, de copier, d'�tudier, de distribuer et de modifier Open ERP librement."

;LangString LicenseNext ${LANG_ENGLISH} "Next >"
;LangString LicenseNext ${LANG_CATALAN} "Següent >"
;LangString LicenseNext ${LANG_SPANISH} "Siguiente >"

LangString SelectLanguageText ${LANG_ENGLISH} "Please, select installer language."
LangString SelectLanguageText ${LANG_CATALAN} "Si us plau, seleccioneu l'idioma per l'instal·lador."
LangString SelectLanguageText ${LANG_SPANISH} "Por favor, seleccione el idioma para el instalador."
LangString SelectLanguageText ${LANG_ITALIAN} "Selezionare il linguaggio di installazione."

LangString SelectLanguageTitleText ${LANG_ENGLISH} "Installer Language"
LangString SelectLanguageTitleText ${LANG_CATALAN} "Idioma de l'instal·ador"
LangString SelectLanguageTitleText ${LANG_SPANISH} "Idioma del instalador"
LangString SelectLanguageTitleText ${LANG_ITALIAN} "Lingua dell'installatore"

LangString FinishPageText ${LANG_ENGLISH} "Start Koo"
LangString FinishPageText ${LANG_CATALAN} "Inicia el Koo"
LangString FinishPageText ${LANG_SPANISH} "Iniciar Koo"
LangString FinishPageText ${LANG_ITALIAN} "Avvia Koo"

LangString DESC_SecKoo ${LANG_ENGLISH} "Koo."
LangString DESC_SecKoo ${LANG_CATALAN} "Koo."
LangString DESC_SecKoo ${LANG_SPANISH} "Koo."
LangString DESC_SecKoo ${LANG_ITALIAN} "Koo."

LangString CannotInstallText ${LANG_ENGLISH} "Can not install the Open ERP Client because a previous installation already exists on this system. Please uninstall your current installation and relaunch this setup wizard."
LangString CannotInstallText ${LANG_CATALAN} "No es pot instal·lar el Koo perquè ja hi ha instal·lada una versió anterior. Si us plau, desinstal·leu la versió actual i reinicieu aquest instal·lador."
LangString CannotInstallText ${LANG_SPANISH} "No se puede instalar Koo porqué ya hay instalada un versión anterior. Por favor, desinstale la versión actual y reinicie este instalador."
LangString CannotInstallText ${LANG_ITALIAN} "Impossibile installare il client OpenERP Koo. Una installazione precedente � presente nel sistema. Disinstallare la versione precedente prima di installare questa."
