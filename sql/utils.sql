--Just something to help out if you're using ogr2ogr to put your GeoJSON
--into PostGIS! More will be added as I find them necessary...

ALTER TABLE cas_crashes
ADD COLUMN crash_date timestamp with time zone;

UPDATE cas_crashes
SET crash_date = to_timestamp(unixt::bigint/1000);

SELECT * FROM cas_crashes LIMIT 10;
