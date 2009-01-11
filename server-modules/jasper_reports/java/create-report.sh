#!/bin/bash

scriptdir=$(dirname "$0")
serverdir=$HOME"/Projectes/openerp-server/bin/addons"
#serverdir=.
if [ "$1" = "--compile" ]; then
	compile="true"
	makejasper="true"
	report="$2"
	xml="$3"
	output="$4"
	dsn="$5"
	user="$6"
	password="$7"
	params="$8"
else
	compile="false"
	makejasper="true"
	report="$1"
	xml="$2"
	output="$3"
	dsn="$4"
	user="$5"
	password="$6"
	params="$7"
fi

echo $compile $makejasper $report $xml $output $dsn $user $password $params
pushd $scriptdir

export JAVA_HOME=/usr/lib/jvm/java-6-sun-1.6.0.10/bin/
export PATH="$JAVA_HOME"/bin:/bin:/usr/bin
export CLASSPATH=$(ls -1 lib/* | grep jar$ | awk '{printf "%s:", $1}')
export CLASSPATH="$CLASSPATH":$scriptdir

rm *.class

java -version
javac -g ReportCompiler.java
javac -g ReportCreator.java
rm "$serverdir/$report.jasper"
ls -la "$serverdir/$report*"
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

