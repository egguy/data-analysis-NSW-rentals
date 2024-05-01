import topojson as tp
import geopandas as gpd

# geopands import with auto detection
postcodes = gpd.read_file("data/shp/suburbs/Suburb.shp", engine="pyogrio")
postcodes.dropna()
# cleanup of the postcode
postcodes['postcode'] = postcodes['postcode'].astype(str)
postcodes['postcode'] = postcodes['postcode'].str.replace(".0", "")
postcodes['postcode'] = postcodes['postcode'].str.zfill(4)
# Fuse the zip codes
postcodes = postcodes.dissolve(by="postcode").reset_index()

# Simplify the geometry
topo = tp.Topology(postcodes).toposimplify(0.00001
                                           , simplify_with='simplification',
                                           simplify_algorithm='vw')

# export to topojson
topo.to_json("data/shp/suburbs/suburb.geojson")
