package com.nantic.jasperreports;

import java.util.Hashtable;

/*
This class overrides Hashtable's get() function to return 
the default language when the language (key) doesn't exist.
*/
public class LanguageTable extends Hashtable {
	private String defaultLanguage;

	public LanguageTable(String defaultLanguage) {
		super();
		this.defaultLanguage = defaultLanguage;
	}
	public Object get(Object key) {
		if ( containsKey(key) )
			return super.get(key);
		else
			return super.get(defaultLanguage);
	}
}


