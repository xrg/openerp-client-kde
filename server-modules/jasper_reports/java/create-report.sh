#!/bin/bash

scriptdir=$(dirname "$0")
#serverdir=.
if [ "$1" = "--compile" ]; then
	compile="true"
	makejasper="true"
	serverdir="$2"
	report="$3"
	xml="$4"
	output="$5"
	dsn="$6"
	user="$7"
	password="$8"
	params="$9"
else
	compile="false"
	makejasper="true"
	serverdir="$1"
	report="$2"
	xml="$3"
	output="$4"
	dsn="$5"
	user="$6"
	password="$7"
	params="$8"
fi

echo "SERVERDIR: ", $serverdir
echo $compile $makejasper $report $xml $output $dsn $user $password $params
pushd $scriptdir


if [ -z "$JAVA_HOME" ]; then
	directories = "/usr/lib/jvm/java-6-sun-1.6.0.10/bin/" "/usr/lib/j2sdk1.6-sun" "/usr/lib/j2sdk1.5-sun"
	for d in directories; do
		if [ -d "$d" ]; then
			export JAVA_HOME="$d"
		fi
	done
fi
export PATH="$JAVA_HOME"/bin:/bin:/usr/bin
export CLASSPATH=$(ls -1 lib/* | grep jar$ | awk '{printf "%s:", $1}')
export CLASSPATH="$CLASSPATH":$scriptdir

rm -f *.class

java -version
javac -g ReportCompiler.java
javac -g ReportCreator.java
rm -f "$serverdir/$report.jasper"
java ReportCompiler "$serverdir/$report.jrxml" "$serverdir/$report.jasper"
java ReportCreator "$serverdir/$report.jasper" "$xml" "$output" "$dsn" "$user" "$password" "$params"

exit

if [ ! -f "ReportCreator.class" ]; then
	compile="true"
fi

if [ ! -f "ReportCompiler.class" ]; then
	echo "Compiling ReportCompiler.java ..."
	javac -g ReportCompiler.java
	echo "Result: $?"
fi

if [ "$compile" = "true" ]; then
	echo "Compiling ReportCreator.java ..."
	javac -g ReportCreator.java
	echo "Result: $?"
fi

if [ "$makejasper" = "true" ]; then
	echo "Creating $report.jasper ..."
	java ReportCompiler "$serverdir/$report.jrxml" "$serverdir/$report.jasper"
	echo "Resultat: $?"
fi

echo "Creating report..."
java ReportCreator "$serverdir/$report.jasper" "$xml" "$output" "$dsn" "$user" "$password" "$params"
echo "Result: $?"
echo $0

popd

