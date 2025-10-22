import streamlit as st
st.set_page_config(layout="wide")
st.title("Streamlit App")
st.header("Hello, Geographers!")

import sys
import tempfile
import os
import zipfile
import subprocess

# try to ensure leafmap is available
try:
    import leafmap.foliumap as leafmap
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "leafmap"])
    import leafmap.foliumap as leafmap

st.sidebar.title("Map controls")

# Basemap selector
basemaps = ["OpenTopoMap", "Esri.WorldImagery", "CartoDB.DarkMatter"]
basemap = st.sidebar.selectbox("Select basemap", basemaps, index=0)

# Vector layer uploader (GeoJSON or zipped Shapefile)
st.sidebar.subheader("Vector layer (GeoJSON or zipped Shapefile)")
vector_file = st.sidebar.file_uploader(
    "Upload GeoJSON (.geojson/.json) or zipped Shapefile (.zip)",
    type=["geojson", "json", "zip"],
)

# COG (Cloud Optimized GeoTIFF) input
st.sidebar.subheader("COG layer (DEM)")
cog_url = st.sidebar.text_input(
    "COG URL (optional)",
    value="",
    help="Enter a public COG URL (optional). Example: https://your-bucket/path/to/dem.tif",
)

# Create the map
m = leafmap.Map(center=[20, 0], zoom=2, basemap=basemap)

# Handle uploaded vector
if vector_file is not None:
    fname = vector_file.name.lower()
    with tempfile.TemporaryDirectory() as tmpdir:
        if fname.endswith((".geojson", ".json")):
            path = os.path.join(tmpdir, vector_file.name)
            with open(path, "wb") as f:
                f.write(vector_file.getbuffer())
            try:
                m.add_geojson(path, layer_name="Uploaded GeoJSON")
                st.sidebar.success(f"Loaded GeoJSON: {vector_file.name}")
            except Exception as e:
                st.sidebar.error(f"Failed to load GeoJSON: {e}")
        elif fname.endswith(".zip"):
            zip_path = os.path.join(tmpdir, vector_file.name)
            with open(zip_path, "wb") as f:
                f.write(vector_file.getbuffer())
            try:
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                # find the .shp file
                shp_path = None
                for root, _, files in os.walk(tmpdir):
                    for f in files:
                        if f.lower().endswith(".shp"):
                            shp_path = os.path.join(root, f)
                            break
                    if shp_path:
                        break
                if shp_path:
                    m.add_shapefile(shp_path, layer_name="Uploaded Shapefile")
                    st.sidebar.success(f"Loaded Shapefile: {os.path.basename(shp_path)}")
                else:
                    st.sidebar.error("No .shp found in the uploaded zip")
            except Exception as e:
                st.sidebar.error(f"Failed to extract/load shapefile: {e}")
        else:
            st.sidebar.error("Unsupported file type")

# Handle COG layer
if cog_url and cog_url.strip():
    try:
        m.add_cog_layer(cog_url.strip(), name="COG DEM")
        st.sidebar.success("Added COG layer")
    except Exception as e:
        st.sidebar.error(f"Failed to add COG: {e}")
else:
    st.sidebar.info("Provide a COG URL to load a raster DEM layer (optional)")

# Add layer control
m.add_layer_control()

# Render the map full-width
m.to_streamlit(height=700)
# ...existing code...