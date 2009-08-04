#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (c) 2006 Nuxeo SARL <http://nuxeo.com>
# Authors : Laurent Godard <lgodard@indesko.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""helper tools for using pyUNO"""

import sys
try:
	import uno, unohelper
	from com.sun.star.connection import NoConnectException
	from com.sun.star.beans import PropertyValue
	isOpenOfficeAvailable = True
except:
	isOpenOfficeAvailable = False

class OpenOffice:
    """helper tools for using pyUNO"""
    def __init__(self, host=None, port=None):
	self.host = host or 'localhost'
	self.port = port or 2002
        self.ctx, self.desktop = self.connect()
        self.oCoreReflection = None

    @staticmethod
    def start(host=None, port=None):
	import subprocess
	host = host or 'localhost'
	port = port or 2002
	subprocess.call(["soffice", "-accept=socket,host=%s,port=%d;urp;" % (host, port), "-nodefault"], shell=False)

    def connect(self):
        """Connection to OOo instance using pyUNO"""
 
        # Uno component context
        localoContext = uno.getComponentContext()
        # create UnoUrlResolver
        resolver = localoContext.ServiceManager.createInstanceWithContext(
                                    "com.sun.star.bridge.UnoUrlResolver",
                                    localoContext )
        # connection 
        try:
            oContext = resolver.resolve(
            "uno:socket,host=%s,port=%i;urp;StarOffice.ComponentContext" % 
                                                      (self.host, self.port))
        except NoConnectException:
            oContext = None
        
        # main desktop object
        if oContext is not None:
            smgr = oContext.ServiceManager
            desktop = smgr.createInstanceWithContext(
                                "com.sun.star.frame.Desktop",
                                oContext)
        else:
            desktop = None
                                    
        return oContext, desktop
    
    def closeAll(self, close_desktop = False):
        """ close all components and terminates desktop if requested"""
        enum = self.desktop.Components.createEnumeration()
        while enum.hasMoreElements():
            elem = enum.nextElement()
            try:
                elem.close(False)
            except AttributeError:
                if not elem.supportsService("com.sun.star.frame.StartModule"):
                    elem.terminate()
        if close_desktop:    
            self.desktop.terminate()
        return
        
    #----------------------------------------
    #   Danny's stuff to make programming less convenient.
    #   http://www.oooforum.org/forum/viewtopic.phtml?t=9115 
    #----------------------------------------

    def getServiceManager( self ):
        """Get the ServiceManager from the running OpenOffice.org.
        """
        return self.ctx.ServiceManager
   
    def createUnoService( self, cClass ):
        """A handy way to create a global objects within the running OOo.
        """
        oServiceManager = self.getServiceManager()
        oObj = oServiceManager.createInstance( cClass )
        return oObj
   
    def getDesktop( self ):
        """An easy way to obtain the Desktop object from a running OOo.
        """
        if self.desktop == None:
            self.desktop = self.createUnoService("com.sun.star.frame.Desktop")
        return self.desktop

    def getCoreReflection( self ):
        if self.oCoreReflection == None:
            self.oCoreReflection = self.createUnoService(
                                    "com.sun.star.reflection.CoreReflection" )
        return self.oCoreReflection 
        
    def createUnoStruct( self, cTypeName ):
        """Create a UNO struct and return it.
        """
        oCoreReflection = self.getCoreReflection()

        # Get the IDL class for the type name
        oXIdlClass = oCoreReflection.forName( cTypeName )

        # Create the struct.
        oReturnValue, oStruct = oXIdlClass.createObject( None )

        return oStruct

    def makePropertyValue( self, cName=None, uValue=None,
                                 nHandle=None, nState=None ):
        """Create a com.sun.star.beans.PropertyValue struct and return it.
        """
        oPropertyValue = self.createUnoStruct(
                                    "com.sun.star.beans.PropertyValue" )

        if cName != None:
            oPropertyValue.Name = cName
        if uValue != None:
            oPropertyValue.Value = uValue
        if nHandle != None:
            oPropertyValue.Handle = nHandle
        if nState != None:
            oPropertyValue.State = nState

        return oPropertyValue 
