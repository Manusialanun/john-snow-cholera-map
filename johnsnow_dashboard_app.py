# johnsnow_dashboard_app.py
import streamlit as st
import folium
from folium.plugins import HeatMap
import geopandas as gpd
import pandas as pd
import os
import tempfile

# Set page configuration
st.set_page_config(
    page_title="John Snow Cholera Dashboard",
    page_icon="💀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("💀 John Snow Cholera Outbreak - 1854")
st.markdown("""
### Interactive Epidemiology Dashboard
Explore the classic cholera map that revolutionized epidemiology and public health.
""")

# Load the data
@st.cache_data
def load_data():
    # Use relative path for deployment
    shapefile_path = r"Data/cholera-deaths"
    
    try:
        deaths_gdf = gpd.read_file(shapefile_path, layer='Cholera_Deaths')
        pumps_gdf = gpd.read_file(shapefile_path, layer='Pumps')
        
        # Convert to WGS84 if needed
        if deaths_gdf.crs and deaths_gdf.crs != 'EPSG:4326':
            deaths_gdf = deaths_gdf.to_crs('EPSG:4326')
        if pumps_gdf.crs and pumps_gdf.crs != 'EPSG:4326':
            pumps_gdf = pumps_gdf.to_crs('EPSG:4326')
            
        return deaths_gdf, pumps_gdf
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

deaths_gdf, pumps_gdf = load_data()

if deaths_gdf is not None and pumps_gdf is not None:
    # Calculate center coordinates
    center_lat = deaths_gdf.geometry.y.mean()
    center_lon = deaths_gdf.geometry.x.mean()
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    st.sidebar.subheader("Map Layers")
    show_heatmap = st.sidebar.checkbox("Show Heatmap", value=True)
    show_skeletons = st.sidebar.checkbox("Show Skeleton Markers", value=True)
    show_pump_labels = st.sidebar.checkbox("Show Pump Labels", value=True)
    
    st.sidebar.subheader("Heatmap Settings")
    heatmap_radius = st.sidebar.slider("Heatmap Radius", 10, 30, 15)
    heatmap_blur = st.sidebar.slider("Heatmap Blur", 5, 20, 10)
    heatmap_opacity = st.sidebar.slider("Heatmap Opacity", 0.1, 1.0, 0.6)
    
    # Create the map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles='OpenStreetMap',
        width='100%',
        height=600
    )
    
    # Add heatmap if enabled
    if show_heatmap:
        heat_data = []
        for idx, row in deaths_gdf.iterrows():
            if hasattr(row.geometry, 'x') and hasattr(row.geometry, 'y'):
                lat, lon = row.geometry.y, row.geometry.x
            else:
                lat, lon = row.geometry.coords[0][1], row.geometry.coords[0][0]
            
            weight = row['Count'] if 'Count' in row else 1
            heat_data.append([lat, lon, weight])
        
        HeatMap(
            heat_data,
            min_opacity=0.3,
            max_opacity=heatmap_opacity,
            radius=heatmap_radius,
            blur=heatmap_blur,
            gradient={0.2: 'orange', 0.5: 'red', 0.8: 'darkred'}
        ).add_to(m)
    
    # Add skeleton markers if enabled
    if show_skeletons:
        for idx, row in deaths_gdf.iterrows():
            if hasattr(row.geometry, 'x') and hasattr(row.geometry, 'y'):
                lat, lon = row.geometry.y, row.geometry.x
            else:
                lat, lon = row.geometry.coords[0][1], row.geometry.coords[0][0]
            
            popup_text = f"<b>Cholera Death #{idx+1}</b>"
            if 'Count' in row:
                popup_text += f"<br>Count: {row['Count']}"
            
            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                icon=folium.DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                    html='<div style="font-size: 18px; color: #696969; opacity: 0.9;">💀</div>'
                ),
                tooltip=f"Cholera Death {idx+1}"
            ).add_to(m)
    
    # Add water pumps
    for idx, row in pumps_gdf.iterrows():
        if hasattr(row.geometry, 'x') and hasattr(row.geometry, 'y'):
            lat, lon = row.geometry.y, row.geometry.x
        else:
            lat, lon = row.geometry.coords[0][1], row.geometry.coords[0][0]
        
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>Water Pump #{idx+1}</b>",
            icon=folium.Icon(color='green', icon='cog', prefix='fa'),
            tooltip=f"Water Pump {idx+1}"
        ).add_to(m)
        
        # Add pump labels if enabled
        if show_pump_labels:
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(0, 0),
                    html=f'<div style="font-size: 12pt; font-weight: bold; color: green; background-color: white; padding: 2px 5px; border: 1px solid green; border-radius: 3px;">Pump {idx+1}</div>'
                )
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Save map to HTML and display using Streamlit
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            m.save(f.name)
            html_string = open(f.name, 'r', encoding='utf-8').read()
        
        st.components.v1.html(html_string, height=600)
    
    with col2:
        st.subheader("📊 Outbreak Statistics")
        st.metric("Total Cholera Deaths", len(deaths_gdf))
        st.metric("Water Pumps", len(pumps_gdf))
        
        st.subheader("🎯 Legend")
        st.markdown("""
        - 💀 **Dark Silver**: Cholera Deaths
        - ⚙️ **Green**: Water Pumps
        - 🔥 **Heatmap**: Death Density
          - Orange: Low density
          - Red: High density
        """)
        
        st.subheader("📖 Historical Context")
        st.markdown("""
        Dr. John Snow's 1854 cholera map demonstrated that cholera was 
        spread through contaminated water, not "bad air" (miasma theory).
        
        This groundbreaking work laid the foundation for modern epidemiology.
        """)
        
else:
    st.error("Could not load the data. Please check if the data folder exists.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This dashboard recreates John Snow's classic 1854 cholera map using modern geospatial tools.

**Live Dashboard:** [Your Streamlit Link]

**Tools used:**
- Python
- GeoPandas
- Folium
- Streamlit
""")
