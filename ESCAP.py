import streamlit as st
from leafmap.foliumap import Map
import geopandas as gpd
import folium
import pandas as pd
from shapely.geometry import Polygon, Point
from streamlit_folium import st_folium
import base64
from PIL import Image
import time
import warnings
import os
import glob
import rasterio
import numpy as np
from folium.raster_layers import ImageOverlay


st.set_page_config(layout="wide")


if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False

logo_path = os.path.join("logo", "escap_logo.png")

def parse_season_files_from_folder(folder_path):
    """
    Parses .tif files in a folder and returns:
    - Sorted list of season labels like '06 - 09' or 'JJAS'
    - A dict mapping season label → full file path
    """

    tif_files = glob.glob(os.path.join(folder_path, "*.tif"))
    season_options = []
    filename_map = {}

    for f in tif_files:
        fname = os.path.basename(f)[:-4]  # Remove .tif
        parts = fname.split("_")
        if len(parts) >= 3:
            season = f"{parts[-2]} - {parts[-1]}"
        elif len(parts) >= 2:
            season = parts[-1]
        else:
            continue
        season_options.append(season)
        filename_map[season] = f

    return sorted(set(season_options)), filename_map


def generate_rgba_array_from_raster(raster_path):
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        bounds = src.bounds

        # Mask nodata and invalid values
        data = np.where((data == src.nodata) | np.isnan(data), np.nan, data)

        # Calculate stats
        mean = np.nanmean(data)
        std = np.nanstd(data)
        min_val = np.nanmin(data)
        max_val = np.nanmax(data)

        # Classification thresholds
        thresholds = [min_val, mean - 2*std, mean, mean + 2*std, max_val]
        colors = [
            (255, 255, 204, 200),  # Pale yellow
            (161, 218, 180, 200),  # Aqua green
            (65, 182, 196, 200),   # Teal
            (34, 94, 168, 200),    # Dark blue
        ]

        # Create RGBA image
        rgba = np.zeros((*data.shape, 4), dtype=np.uint8)
        for i in range(4):
            mask = (data >= thresholds[i]) & (data < thresholds[i+1])
            rgba[mask] = colors[i]

        # Return image and bounds
        extent = [[bounds.bottom - 0.15, bounds.left], [bounds.top - 0.12, bounds.right]]
        return rgba, extent




    

if not st.session_state.splash_shown:
    with open(logo_path, "rb") as img_file:
        encoded_logo = base64.b64encode(img_file.read()).decode()

    st.markdown("""
        <style>
        .splash-container {{
            position: fixed;
            z-index: 99999;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            animation: fadeOut 1s ease-out 2.5s forwards;
        }}

        .splash-logo {{
            height: 200px;
            opacity: 0;
            animation: fadeInScale 1.5s ease-in-out forwards;
        }}

        @keyframes fadeInScale {{
            0% {{
                opacity: 0;
                transform: scale(0.7);
            }}
            100% {{
                opacity: 1;
                transform: scale(1);
            }}
        }}

        @keyframes fadeOut {{
            to {{
                opacity: 0;
                visibility: hidden;
            }}
        }}
        </style>

        <div class="splash-container">
            <img src="data:image/png;base64,{}" class="splash-logo"/>
        </div>
    """.format(encoded_logo), unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.splash_shown = True
    st.rerun()
    time.sleep(0.1)

else:
    
    # === Custom CSS Styling ===
    st.markdown("""
        <style>
        body {
            background-color: white;
            color: black;
        }
        .block-container {
            padding-top: 2.5rem !important;
        }
        .header-section {
            display: flex;
            align-items: center;
            background-color: white;
            border-bottom: 1px solid #ccc;
            padding: 0.75rem 1.2rem;
            margin: 0;
            width: 100%;
            height: 3.5rem;
            z-index: 100;
        }
        .header-logo {
            height: 30px;
            margin-right: 0.75rem;
        }
        .header-title {
            font-size: 28px;
            font-weight: 600;
            text-align: center;
            flex-grow: 1;
            color: #0b5ed7;
        }
        .css-1aumxhk {
            padding-top: 0 !important;
        }
        .stSidebar {
            background-color: white !important;
            border-right: 1px solid #ccc;
            padding-top: 5rem;
        }
        .stButton > button {
            background-color: #0b5ed7;
            color: white;
            border-radius: 5px;
            font-weight: bold;
            border: none;
        }
        .stButton > button:hover {
            color: white !important;
            background-color: #094db3 !important;
        }
        .dashboard-btn > button {
            background-color: #009edb;
            color: white;
            font-weight: bold;
            border-radius: 4px;
            border: none;
        }
        .dashboard-btn > button:hover {
            color: white !important;
            background-color: #007cad !important;
        }
        /* Remove default Streamlit padding */
        .main .block-container {
            padding: 0 !important;
            padding-top: 2.5rem !important;
            padding-left: 1rem !important;
            margin: 0 !important;
        }
    
        /* Remove container margin */
        .element-container:has(.leaflet-container) {
            padding: 0 !important;
            margin: 0 !important;
        }
    
        /* Make folium map take full height and width */
        .leaflet-container {
            height: 100vh !important;
            width: 100vw !important;
            margin: 0 !important;
            padding: 0 !important;
        }
    
        /* Prevent scrollbars or body overflow */
        html, body {
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        div.stButton > button#styled_reset_btn {
            background-color: #dc3545; /* Bootstrap danger red */
            color: white;
            font-weight: bold;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            width: 100%;
            margin-top: 1rem;
        }
        div.stButton > button#styled_reset_btn:hover {
            background-color: #b02a37 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    
    # === Session State Initialization ===
    defaults = {
        "show_left_panel": None,
        "show_dashboard": False,
        "dashboard_expanded": False,
        "hazard_selected": False,
        "agri_selected": False,
        "energy_selected": False,
        "visible_layers": {},
        "opacity": {},
        "selected_basemap": "OpenStreetMap",
        "selected_region": None,
        "last_zoomed_region": None,
        "legend_rerun_triggered": False,
        "show_compare": False,
        "compare_region_1": None,
        "compare_region_2": None,
    }
    
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    
    
    
    # === Header with Logo and Title ===
    
    
    # Load and encode the image as base64
    logo_path = os.path.join("logo", "escap_logo.png")
    logo_image = Image.open(logo_path)
    
    # Display custom header using columns
    header_cols = st.columns([1, 5, 1])
    with header_cols[0]:
        st.image(logo_image, use_column_width="auto", output_format="PNG")
    
    with header_cols[1]:
        st.markdown(
            "<h2 style='text-align: center; color: #0b5ed7; margin-top: 0.5rem;'>Agriculture and Energy Risk Explorer</h2>",
            unsafe_allow_html=True
        )
    
    with header_cols[2]:
        st.write("")  # spacer
    
    
    def reset_all():
        keys_to_reset = [
            "show_left_panel",
            "show_dashboard",
            "dashboard_expanded",
            "hazard_selected",
            "agri_selected",
            "energy_selected",
            "visible_layers",
            "opacity",
            "selected_basemap",
            "selected_region",
            "last_zoomed_region",
            "legend_rerun_triggered",
            "show_compare",
            "compare_region_1",
            "compare_region_2",
            "show_reset_confirm",
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.splash_shown = True
        st.rerun()
 
    
    # === Sidebar Buttons & Legends ===
    with st.sidebar:
        st.markdown("""
            <style>
                section[data-testid="stSidebar"] {
                    background-color: white;
                    border-right: 2px solid #ccc;
                    padding: 1rem;
                    padding-top: 5rem;
                }
                div.stButton > button {
                    background-color: #0b5ed7;
                    color: white;
                    font-weight: bold;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 5px;
                    width: 100%;
                    margin-bottom: 0.5rem;
                }
                div.stButton > button:hover,
                div.stButton > button:focus,
                div.stButton > button:active {
                    background-color: #084298 !important;
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)
    
        # Sidebar Top Buttons
        if st.button("Basemap"):
            st.session_state.show_left_panel = "Basemap"
    
        if st.button("Region"):
            st.session_state.show_left_panel = "Region"
    
        if st.button("Climate"):
            st.session_state.show_left_panel = "Hazard"
    
        if st.button("Agriculture"):
            st.session_state.show_left_panel = "Agriculture"
    
        if st.button("Energy"):
            st.session_state.show_left_panel = "Energy"
    
        if st.button("Dashboard"):
            if st.session_state.dashboard_expanded:
                st.session_state.dashboard_expanded = False
                st.session_state.show_dashboard = False
            elif st.session_state.show_dashboard:
                st.session_state.show_dashboard = False
            else:
                st.session_state.show_dashboard = True

        if st.button("Reset App", key="styled_reset_btn"):
            st.session_state.show_reset_confirm = True

        if st.session_state.get("show_reset_confirm"):
            with st.container():
                st.warning("Are you sure you want to reset all selections?")
                confirm_col, cancel_col = st.columns([1, 1])
                with confirm_col:
                    if st.button("✅ Yes, Reset", key="confirm_reset_btn"):
                        reset_all()
                with cancel_col:
                    if st.button("❌ Cancel", key="cancel_reset_btn"):
                        st.session_state.show_reset_confirm = False


        st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    
        # === Legends Section ===
        if st.session_state.visible_layers:
            st.markdown("---")
            st.markdown("### Legends")
            keys_to_remove = []
        
            for key, label in list(st.session_state.visible_layers.items()):
                if key == "Basemap":
                    continue

                row = st.columns([0.55, 0.35, 0.1])
                
                # Show Layer Checkbox
                with row[0]:
                    show = st.checkbox(label, value=st.session_state.opacity.get(key, 1.0) > 0, key=f"{key}_chk_sidebar")
        
                # Opacity Slider (if visible)
                with row[1]:
                    if show:
                        st.session_state.opacity[key] = st.slider(
                            "", 0.0, 1.0,
                            st.session_state.opacity.get(key, 1.0),
                            0.05,
                            key=f"{key}_opacity_sidebar",
                            label_visibility="collapsed"
                        )
                    else:
                        # Set opacity to 0.0 to hide without removing
                        st.session_state.opacity[key] = 0.0
        
                # ❌ Remove Button
                with row[2]:
                    if st.button("❌", key=f"{key}_remove_sidebar"):
                        keys_to_remove.append(key)
        
                st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
        
            # Apply all removals in batch to avoid rerun during loop
            if keys_to_remove:
                for key in keys_to_remove:
                    st.session_state.visible_layers.pop(key, None)
                    st.session_state.opacity.pop(key, None)
                    if key == st.session_state.show_left_panel:
                        st.session_state.show_left_panel = None
                st.session_state.legend_rerun_flag = True
        
        # Trigger a one-time rerun only after layer removal
        if st.session_state.get("legend_rerun_flag"):
            st.session_state.legend_rerun_flag = False
            st.rerun()
    
               
    
    
    
    
    # === Load region shapefile only once ===
    if "region_gdf" not in st.session_state:
        region_path = os.path.join("Adm", "BNDA1_MNG_2002-01-01_lastupdate.shp")
        st.session_state.region_gdf = gpd.read_file(region_path).to_crs(epsg=4326)
    
    region_names = sorted(st.session_state.region_gdf["adm1nm"].dropna().unique())
    
    # === Layout Configuration ===
    map_col_width = 12
    if st.session_state.show_left_panel:
        map_col_width -= 3
    if st.session_state.show_dashboard:
        map_col_width -= 3
    
    # Main layout depending on open panels
    if st.session_state.dashboard_expanded and st.session_state.show_left_panel:
        layout = st.columns([3, 9])
    elif st.session_state.dashboard_expanded:
        layout = st.columns([12])
    elif st.session_state.show_left_panel and st.session_state.show_dashboard:
        layout = st.columns([3, map_col_width, 3])
    elif st.session_state.show_left_panel:
        layout = st.columns([3, map_col_width])
    elif st.session_state.show_dashboard:
        layout = st.columns([map_col_width, 3])
    else:
        layout = st.columns([12])
    
    
    
    
    
     
    
    
    # === Left Options Panel ===
    if st.session_state.show_left_panel:
        with layout[0]:
            row = st.columns([5, 1])
            with row[0]:
                st.markdown("## Options")
            with row[1]:
                if st.button("◀", key="hide_panel_btn"):
                    st.session_state.show_left_panel = None
                    st.rerun()
    
            def add_layer(key, label, opacity=0.5):
                # If trying to re-add same layer, do nothing
                if key in st.session_state.visible_layers and st.session_state.visible_layers[key] == label:
                    return
            
                # If key is 'Hazard', remove previous one
                if key == "Hazard":
                    if "Hazard" in st.session_state.visible_layers:
                        del st.session_state.visible_layers["Hazard"]
                        st.session_state.opacity.pop("Hazard", None)
            
                # Now add the new one
                st.session_state.visible_layers[key] = label
                st.session_state.opacity[key] = opacity
                st.session_state.legend_rerun_triggered = True

               


            if st.session_state.show_left_panel == "Hazard":
                base_path = os.path.join("Climate")
    
                variable = st.selectbox("Select Climate Variable", [
                    "Please select", "Maximum Temperature", "Mean Temperature", "Minimum Temperature", "Precipitation", "Solar Radiation"
                ], key="climate_var_sidebar")
    
                scenario = st.selectbox("Select Scenario", [
                    "Please select", "Historical", "SSP1", "SSP2", "SSP3", "SSP5"
                ], key="climate_scenario_sidebar")
    
                year_range = None
                if scenario != "Please select" and scenario != "Historical":
                    year_range = st.selectbox("Select Year Range", [
                        "Please select", "2021-2040", "2041-2060", "2061-2080", "2081-2100"
                    ], key="climate_year_range_sidebar")
    
                seasonality = None
                if scenario != "Please select":
                    seasonality = st.selectbox("Select Seasonality", [
                        "Please select", "Annual", "Seasonal"
                    ], key="climate_seasonality_sidebar")
    
                # === Handle Annual ===
                if (
                    variable != "Please select" and
                    scenario != "Please select" and
                    (scenario == "Historical" or (year_range and year_range != "Please select")) and
                    seasonality == "Annual"
                ):
                    # Build folder path
                    path_parts = [base_path, variable, scenario]
                    if scenario != "Historical":
                        path_parts.append(year_range)
                    path_parts.append("Annual")
                    annual_folder = os.path.join(*path_parts)
                
                    tif_files = glob.glob(os.path.join(annual_folder, "*.tif"))
                
                    if tif_files:
                        # Pick the first tif for now (you can later add a selector if multiple)
                        selected_tif = os.path.basename(tif_files[0])  # or add dropdown for multiple
                        label = f"{variable} - {scenario}" if scenario == "Historical" else f"{variable} - {scenario} - {year_range}"
                        add_layer("Hazard", label)
                        st.session_state.selected_hazard_file = tif_files[0]
                    else:
                        st.warning("No annual .tif file found in: " + annual_folder)
                
                # === Handle Seasonal ===
                elif (
                    variable != "Please select" and
                    scenario != "Please select" and
                    (scenario == "Historical" or (year_range and year_range != "Please select")) and
                    seasonality == "Seasonal"
                ):
                    path_parts = [base_path, variable, scenario]
                    if scenario != "Historical":
                        path_parts.append(year_range)
                    path_parts.append("Seasonal")
                    seasonal_folder = os.path.join(*path_parts)
                
                    if os.path.exists(seasonal_folder):
                        season_options, filename_map = parse_season_files_from_folder(seasonal_folder)
                    
                        selected_season = st.selectbox("Select Season", ["Please select"] + season_options, key="climate_season_choice")
                    
                        if selected_season != "Please select":
                            label = f"{variable} - {scenario}" if scenario == "Historical" else f"{variable} - {scenario} - {year_range}"
                            label += f" - {selected_season}"
                            add_layer("Hazard", label)
                            st.session_state.selected_hazard_file = filename_map[selected_season]
                    else:
                        st.warning("No seasonal folder found: " + seasonal_folder)

    
    



            
            elif st.session_state.show_left_panel == "Basemap":
                options = [
                    "Please select from dropdown:", 
                    "No Basemap", 
                    "OpenStreetMap", 
                    "CartoDB.Positron", 
                    "CartoDB.DarkMatter", 
                    "Stamen.Terrain", 
                    "Stamen.Toner"
                ]
                selected = st.selectbox("Select Basemap", options, key="basemap_select_sidebar")
            
                # Only update if there's a change
                if selected != "Please select" and selected != st.session_state.get("selected_basemap"):
                    st.session_state.selected_basemap = selected
            
                    # Clear previous basemap from legend if any
                    st.session_state.visible_layers.pop("Basemap", None)
                    st.session_state.opacity.pop("Basemap", None)
            
                    # Add new basemap only if not "No Basemap"
                    if selected != "No Basemap":
                        st.session_state.visible_layers["Basemap"] = selected
                        st.session_state.opacity["Basemap"] = 1.0
            


    
            elif st.session_state.show_left_panel == "Region":
                region_names_with_default = ["Please select from dropdown:"] + region_names
                selected = st.selectbox("Select a region", region_names_with_default, key="region_select_sidebar")
                if selected != "Please select from dropdown:":
                    st.session_state.selected_region = selected
    
            elif st.session_state.show_left_panel == "Agriculture":
                crop = st.selectbox("Select Crop", ["Please select from dropdown:", "Rice", "Wheat"], key="agri_crop_sidebar")
                detail = st.selectbox("Select Layer", ["Please select from dropdown:", "Irrigated", "Rainfed", "Production"], key="agri_layer_sidebar")
                if crop != "Please select from dropdown:" and detail != "Please select from dropdown:":
                    st.session_state.agri_selected = True
                    st.session_state.energy_selected = False
                    st.session_state.visible_layers.pop("Energy", None)
                    st.session_state.opacity.pop("Energy", None)
                    add_layer("Agriculture", f"{crop} - {detail}")
    
            elif st.session_state.show_left_panel == "Energy":
                base_energy_path = os.path.join("Energy")
            
                if os.path.exists(base_energy_path):
                    energy_folders = [
                        f for f in os.listdir(base_energy_path)
                        if os.path.isdir(os.path.join(base_energy_path, f))
                    ]
            
                    energy_folders.sort()
                    selected_asset = st.selectbox(
                        "Select Energy Asset",
                        ["Please select"] + energy_folders,
                        key="energy_asset_sidebar"
                    )
            
                    if selected_asset != "Please select":
                        selected_asset_path = os.path.join(base_energy_path, selected_asset)
            
                        # Look for .tif or .shp
                        tif_files = glob.glob(os.path.join(selected_asset_path, "*.tif"))
                        shp_files = glob.glob(os.path.join(selected_asset_path, "*.shp"))
            
                        if tif_files:
                            selected_file = tif_files[0]  # take the first tif
                            st.session_state.energy_selected = True
                            st.session_state.agri_selected = False
                            st.session_state.visible_layers.pop("Agriculture", None)
                            st.session_state.opacity.pop("Agriculture", None)
                            st.session_state.selected_energy_file = selected_file
                            add_layer("Energy", selected_asset)
            
                        elif shp_files:
                            selected_file = shp_files[0]  # take the first shapefile
                            st.session_state.energy_selected = True
                            st.session_state.agri_selected = False
                            st.session_state.visible_layers.pop("Agriculture", None)
                            st.session_state.opacity.pop("Agriculture", None)
                            st.session_state.selected_energy_file = selected_file
                            add_layer("Energy", selected_asset)
            
                        else:
                            st.warning("No .tif or .shp file found inside the selected folder.")
                else:
                    st.warning("Energy folder path does not exist.")
    
    
    
    # Trigger a one-time rerun if a new layer was just added
    if st.session_state.legend_rerun_triggered:
        st.session_state.legend_rerun_triggered = False
        st.rerun()
    
    
    
    
    # === Map Column ===
    if not st.session_state.dashboard_expanded:
        map_index = 1 if st.session_state.show_left_panel else 0
        with layout[map_index]:
            selected_base = st.session_state.get("selected_basemap", "OpenStreetMap")
            gdf = st.session_state.region_gdf
            sel_poly = gdf[gdf["adm1nm"] == st.session_state.selected_region] if st.session_state.selected_region else None
    
            if selected_base == "No Basemap":
                m = folium.Map(location=[27.7, 85.3], zoom_start=5, tiles=None)
            else:
                m = folium.Map(location=[27.7, 85.3], zoom_start=5)
                folium.TileLayer(tiles=selected_base, attr="Map data attribution").add_to(m)




            # === Climate Raster Overlay ===
            if "Hazard" in st.session_state.visible_layers and "selected_hazard_file" in st.session_state:
                hazard_raster_path = st.session_state.selected_hazard_file
                if os.path.exists(hazard_raster_path):
                    try:
                        rgba_img, extent = generate_rgba_array_from_raster(hazard_raster_path)
                        folium.raster_layers.ImageOverlay(
                            image=rgba_img,
                            bounds=extent,
                            opacity=st.session_state.opacity.get("Hazard", 1.0),
                            name=st.session_state.visible_layers["Hazard"]
                        ).add_to(m)
                    except Exception as e:
                        st.warning(f"Failed to overlay hazard raster: {e}")
                else:
                    st.warning(f"Hazard file not found: {hazard_raster_path}")




            
            

            # === Energy Layer Overlay (Points with PNG Icon and Tooltip) ===
            if (
                "Energy" in st.session_state.visible_layers and 
                st.session_state.opacity.get("Energy", 1.0) > 0
            ):
                energy_file = st.session_state.get("selected_energy_file")
                if energy_file and energy_file.lower().endswith(".shp") and os.path.exists(energy_file):
                    try:
                        energy_folder = os.path.dirname(energy_file)
            
                        # Find PNG icon in the same folder
                        icon_path = next(
                            (os.path.join(energy_folder, f) for f in os.listdir(energy_folder) if f.lower().endswith(".png")),
                            None
                        )
            
                        gdf_energy = gpd.read_file(energy_file).to_crs("EPSG:4326")
            
                        # Safely find the name field
                        name_field = next((col for col in gdf_energy.columns if col.lower() in ["name", "site_name", "title"]), None)
            
                        for _, row in gdf_energy.iterrows():
                            geom = row.geometry
                            if geom and geom.geom_type == "Point":
                                display_name = str(row[name_field]) if name_field else "Energy Site"
            
                                icon = folium.CustomIcon(
                                    icon_image=icon_path,
                                    icon_size=(30, 30),
                                    icon_anchor=(12, 12)
                                ) if icon_path else folium.Icon(color="red", icon="bolt", prefix="fa")
            
                                folium.Marker(
                                    location=[geom.y, geom.x],
                                    tooltip=display_name,
                                    icon=icon
                                ).add_to(m)
            
                    except Exception as e:
                        st.warning(f"Failed to overlay energy layer: {e}")
            

    
            # === Apply Grey Mask ===
            world = Polygon([(-180, -90), (-180, 90), (180, 90), (180, -90), (-180, -90)])
            world_gdf = gpd.GeoDataFrame(geometry=[world], crs="EPSG:4326")
            mask_geom = world_gdf.geometry[0].difference(sel_poly.unary_union if sel_poly is not None and not sel_poly.empty else gdf.unary_union)
            mask_gdf = gpd.GeoDataFrame(geometry=[mask_geom], crs="EPSG:4326")
    
            folium.GeoJson(
                mask_gdf.__geo_interface__,
                name="Grey Mask",
                style_function=lambda x: {
                    "fillColor": "black",
                    "color": "gray",
                    "weight": 1,
                    "fillOpacity": 0.6
                }
            ).add_to(m)
    
            # === Add Selected Region or All Regions ===
            if sel_poly is not None and not sel_poly.empty:
                folium.GeoJson(
                    data=sel_poly.__geo_interface__,
                    name="Selected Region",
                    style_function=lambda f: {
                        "fillColor": "#transparent",
                        "color": "blue",
                        "weight": 2,
                        "fillOpacity": 0.0,
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["adm1nm"], aliases=["Region:"])
                ).add_to(m)
            else:
                folium.GeoJson(
                    data=gdf,
                    name="Regions",
                    style_function=lambda f: {
                        "fillColor": "transparent",
                        "color": "blue",
                        "weight": 1,
                        "fillOpacity": 0.0,
                    },
                    highlight_function=lambda f: {
                        "color": "orange",
                        "weight": 3,
                        "fillOpacity": 0.6,
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["adm1nm"], aliases=["Region:"])
                ).add_to(m)
    
            # === Auto Zoom & Animation ===
            try:
                bounds = sel_poly.geometry.total_bounds if sel_poly is not None and not sel_poly.empty else gdf.total_bounds
                minx, miny, maxx, maxy = bounds
                m.fit_bounds([[miny, minx], [maxy, maxx]])
    
                if st.session_state.last_zoomed_region == st.session_state.selected_region:
                    zoom_js = folium.Element(f"""
                    <script>
                        var bounds = [[{miny}, {minx}], [{maxy}, {maxx}]];
                        setTimeout(function() {{
                            if (typeof map !== 'undefined') {{
                                map.flyToBounds(bounds, {{
                                    padding: [80, 80],
                                    duration: 6,
                                    easeLinearity: 0.1
                                }});
                            }}
                        }}, 1000);
                    </script>
                    """)
                    m.get_root().html.add_child(zoom_js)
    
                    transition_fx = folium.Element("""
                    <style>
                        .map-transition {
                            animation: fadeZoom 2s ease-in-out;
                        }
                        @keyframes fadeZoom {
                            0% { filter: blur(4px); opacity: 0.4; }
                            50% { filter: blur(2px); opacity: 0.8; }
                            100% { filter: blur(0px); opacity: 1; }
                        }
                    </style>
                    <script>
                        setTimeout(function () {
                            const container = document.querySelector('.leaflet-container');
                            if (container) {
                                container.classList.add('map-transition');
                            }
                        }, 400);
                    </script>
                    """)
                    m.get_root().html.add_child(transition_fx)
                    st.session_state.last_zoomed_region = None
    
            except Exception as e:
                st.warning(f"Zoom failed: {e}")           
    
            # === Display Map ===
            with st.container():
                st.markdown("<div style='margin: -30px;'>", unsafe_allow_html=True)
                map_data = st_folium(m, height=1000, width="100%")
                st.markdown("</div>", unsafe_allow_html=True)
    
            # === Handle Region Click ===
            if map_data and "last_clicked" in map_data and map_data["last_clicked"]:
                lat = map_data["last_clicked"]["lat"]
                lon = map_data["last_clicked"]["lng"]
                clicked_point = Point(lon, lat).buffer(0.01)
    
                match = gdf[gdf.intersects(clicked_point)]
                if not match.empty:
                    region_name = match.iloc[0]["adm1nm"]
                    if st.session_state.selected_region != region_name:
                        st.session_state.selected_region = region_name
                        st.session_state.last_zoomed_region = region_name
                        st.rerun()
    
    # === Dashboard Panel ===
    if st.session_state.show_dashboard or st.session_state.dashboard_expanded:
        # Determine dashboard column index
        if st.session_state.dashboard_expanded:
            dash_col_index = 0 if len(layout) == 1 else 1
        else:
            dash_col_index = -1  # last column by default
    
        with layout[dash_col_index]:
            # Dashboard header row
            row = st.columns([5, 1, 1])
            with row[0]:
                title = "Full Dashboard View" if st.session_state.dashboard_expanded else "Dashboard"
                st.markdown(f"## {title}")
            with row[1]:
                if st.session_state.dashboard_expanded:
                    if st.button("⚊", key="collapse_dashboard_btn"):
                        st.session_state.dashboard_expanded = False
                        st.session_state.show_dashboard = True
                        st.rerun()
                else:
                    if st.button("⛶", key="expand_dashboard_btn"):
                        st.session_state.dashboard_expanded = True
                        st.session_state.show_left_panel = None
                        st.rerun()
            with row[2]:
                if st.button("❌", key="hide_dashboard_btn"):
                    st.session_state.dashboard_expanded = False
                    st.session_state.show_dashboard = False
                    st.rerun()
    
            # Dashboard content logic
            hazard_visible = "Hazard" in st.session_state.visible_layers
            agri_or_energy_visible = "Agriculture" in st.session_state.visible_layers or "Energy" in st.session_state.visible_layers
    
            if not hazard_visible and not agri_or_energy_visible:
                st.warning("Please select climate and agriculture or energy layer")
            elif not hazard_visible:
                st.warning("Please select climate layer")
            elif not agri_or_energy_visible:
                st.warning("Please select agriculture or energy layer")
            else:
                if st.session_state.dashboard_expanded:
                    # === Expanded Dashboard View ===
                    st.markdown("### Exposure Chart")
                    st.bar_chart({
                        "Region A": [300],
                        "Region B": [150],
                        "Region C": [400],
                        "Region D": [200]
                    })
    
                    st.markdown("### Infrastructure Breakdown")
                    df = pd.DataFrame({
                        "Region": ["A", "B", "C", "D"],
                        "Exposed Population": [300, 150, 400, 200],
                        "Infrastructure Impacted": [20, 10, 35, 15],
                        "Hospitals Exposed": [3, 1, 5, 2],
                        "Schools Exposed": [10, 5, 12, 6]
                    })
                    st.dataframe(df)
    
                    st.markdown("### Risk Level Interpretation")
                    st.success("Region C is most exposed due to population and infrastructure density.")
                else:
                    # === Compact Dashboard View ===
                    st.markdown("### Exposure Chart")
                    st.bar_chart({
                        "Region A": [300],
                        "Region B": [150],
                        "Region C": [400]
                    })
    
                    st.markdown("### Underlying Data Table")
                    df = pd.DataFrame({
                        "Region": ["A", "B", "C"],
                        "Exposed Population": [300, 150, 400],
                        "Infrastructure Impacted": [20, 10, 35]
                    })
                    st.dataframe(df)
