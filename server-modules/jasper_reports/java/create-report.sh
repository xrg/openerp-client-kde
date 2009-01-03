#!/bin/bash

scriptdir=$(dirname "$0")

if [ "$1" = "--compile" ]; then
	compile="true"
	makejasper="true"
	report="$2"
	xml="$3"
	output="$4"
else
	compile="false"
	makejasper="false"
	report="$1"
	xml="$2"
	output="$3"
fi

pushd $scriptdir

export JAVA_HOME=/usr/lib/j2sdk1.5-sun
export PATH="$JAVA_HOME"/bin:/bin:/usr/bin
export CLASSPATH=$(ls -1 lib/* | grep jar$ | awk '{printf "%s:", $1}')
export CLASSPATH="$CLASSPATH"$scriptdir

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
	java ReportCompiler $report.jrxml $report.jasper
	echo "Resultat: $?"
fi

echo "Creating report..."
java ReportCreator "$report.jasper" "$xml" "$output"
echo "Result: $?"

echo $0
kpdf $output

popd

