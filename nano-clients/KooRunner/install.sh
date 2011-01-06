#!/bin/bash
zip -r ../koorunner.zip .
rm -R ~/.kde/share/apps/plasma/runners/koorunner
plasmapkg -i ../koorunner.zip
