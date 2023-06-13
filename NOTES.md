# GIS Data

## Convert from GDA94 or GDA2020 to WGS84

```bash
# Read the projection format from the .prj file
ogr2ogr -f "ESRI Shapefile" -s_srs input.prj -t_srs EPSG:4326 output.shp input.shp
```
