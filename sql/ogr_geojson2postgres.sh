#!/bin/bash

# chmod u+x ogr_geojson2postgres.sh

DBNAME="Cycling"
PGUSER="richard"
ogr2ogr -f "PostgreSQL" -gt 1000 PG:"dbname=$DBNAME user=$PGUSER" "data.geojson" -nln cas_crashes
