#!/bin/bash

if [ -z "$JAVA_HOME" ]; then
	directories="/usr/lib/jvm/java-6-sun-1.6.0.10/bin /usr/lib/j2sdk1.6-sun /usr/lib/j2sdk1.5-sun"
	for d in $directories; do
		if [ -d "$d" ]; then
			export JAVA_HOME="$d"
		fi
	done
fi

rm lib/i18n.jar

export PATH="$JAVA_HOME"/bin:/bin:/usr/bin
export CLASSPATH=$(ls -1 lib/* | grep jar$ | awk '{printf "%s:", $1}')
export CLASSPATH="$CLASSPATH":$scriptdir

javac i18n.java I18nGetText.java I18nScriptlet.java I18nGroovyCompiler.java JasperServer.java || exit
rm i18n.jar
jar cvf i18n.jar i18n.class I18nGetText.java I18nGroovyCompiler.class I18nScriptlet.class
mv i18n.jar lib

java JasperServer
