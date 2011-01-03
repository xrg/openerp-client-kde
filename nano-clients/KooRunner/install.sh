#!/bin/bash
zip -r ../koo-fts.zip .
rm -R ~/.kde/share/apps/plasma/runners/openerp-fts
plasmapkg -i ../openerp-fts.zip
