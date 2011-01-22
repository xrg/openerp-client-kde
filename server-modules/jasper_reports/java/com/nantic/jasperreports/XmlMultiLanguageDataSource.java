package com.nantic.jasperreports;

import net.sf.jasperreports.engine.JRRewindableDataSource;
import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.data.JRCsvDataSource;
import net.sf.jasperreports.engine.JRField;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.design.JRDesignField;

import java.io.*;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.Locale;


/*
This class overrides getFieldValue() from JRXmlDataSource to parse
java.lang.Object fields that will come from Python coded with data
for each language.
*/
public class XmlMultiLanguageDataSource extends JRXmlDataSource {
	public XmlMultiLanguageDataSource(String uri, String selectExpression) throws JRException {
		super(uri, selectExpression);
	}

	public Object getFieldValue(JRField jrField) throws JRException {
		Object value;
		if ( jrField.getValueClassName().equals( "java.lang.Object" ) ) {
			JRDesignField fakeField = new JRDesignField();
			fakeField.setName( jrField.getName() );
			fakeField.setDescription( jrField.getDescription() );
			fakeField.setValueClassName( "java.lang.String" );
			fakeField.setValueClass( String.class );
			value = super.getFieldValue( fakeField );

			LanguageTable values = new LanguageTable("en_US");
			String v = (String) value;
			String[] p = v.split( "\\|" );
			for( int j=0; j < p.length ; j++ ) {
				//System.out.println( p[j] );
				String[] map = p[j].split( "~" );
				if ( map.length == 2 ) 
					values.put( map[0], map[1] );
			}
			value = (Object)values;
		} else {
			value = super.getFieldValue(jrField);
		}
		return value;
	}
}


