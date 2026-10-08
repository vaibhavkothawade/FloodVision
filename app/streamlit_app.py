import streamlit as st
import plotly.express as px
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import json
from math import radians, sin, cos, sqrt, atan2
from demo_data import event_data
def calculate_aoi_area(aoi):
    coordinates = aoi["geometry"]["coordinates"][0]

    total = 0

    for i in range(len(coordinates)):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[(i + 1) % len(coordinates)]

        x1 = radians(lon1)
        y1 = radians(lat1)
        x2 = radians(lon2)
        y2 = radians(lat2)

        total += x1 * y2 - x2 * y1

    area = abs(total) / 2

    earth_radius = 6371

    area_km2 = area * earth_radius * earth_radius

    return area_km2
st.set_page_config(
    page_title="FloodLens",
    page_icon="🌊",
    layout="wide"
)
if "drawn_aoi" not in st.session_state:
    st.session_state.drawn_aoi = None

st.title("🌊 FloodLens")
st.subheader("AI Flood Impact Copilot")

st.write(
    "Transforming satellite imagery into prioritized flood impact "
    "maps and actionable incident insights."
)

st.success("● Analysis ready — Flood impact results available")

st.sidebar.header("Controls")
event = st.sidebar.selectbox(
    "Select flood event",
    ["Demo Flood Event 1", "Demo Flood Event 2"]
)
data = event_data[event]

if st.session_state.drawn_aoi:
    data = data.copy()

    aoi_area = calculate_aoi_area(st.session_state.drawn_aoi)

    base_area = data["flood_area"]

    area_ratio = min(aoi_area / base_area, 1)

    data["flood_area"] = round(aoi_area, 1)
    data["buildings"] = max(1, round(data["buildings"] * area_ratio))
    data["roads"] = round(data["roads"] * area_ratio, 1)
    data["population"] = max(1, round(data["population"] * area_ratio))

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Methodology", "About"]
)
if page == "About":
    st.title("About FloodLens")
    st.write(
        "FloodLens is an AI-powered flood impact decision-support "
        "dashboard that combines satellite imagery, flood detection, "
        "GIS risk analysis, and AI-generated incident insights."
    )
    st.stop()

if page == "Methodology":
    st.title("Methodology & Metrics")

    st.markdown("""
    ### Flood Detection
    Satellite imagery is analyzed to identify areas affected by flooding.

    ### Risk Assessment
    Flood-affected areas are combined with buildings, roads, and population data
    to estimate the potential impact.

    ### Priority Ranking
    Zones are ranked according to their estimated flood impact and risk indicators.

    ### AI Incident Briefing
    The detected impact, priority, and model confidence are converted into a
    plain-language incident summary for emergency assessment.
    """)

    st.markdown("### Current Demo Metrics")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric("Flood Area", f'{data["flood_area"]} km²')

    with metric_col2:
        st.metric("Model Confidence", f'{data["confidence"]}%')

    with metric_col3:
        st.metric("Priority", data["priority"])

    st.stop()



before_date = st.sidebar.date_input("Before flood", value=None)
after_date = st.sidebar.date_input("After flood", value=None)
if before_date and after_date and after_date <= before_date:
    st.sidebar.error("After-flood date must be later than the before-flood date.")
    st.stop()

if st.sidebar.button("Run Flood Analysis"):

    st.session_state.analysis_run = True
    st.rerun()

if st.session_state.get("analysis_run", False):
    st.sidebar.success("Analysis completed successfully.")
st.sidebar.markdown("### Area of Interest")

aoi = st.sidebar.selectbox(
    "Select AOI",
    ["Demo flood zone", "Custom AOI"]
)
if st.session_state.drawn_aoi:
    st.sidebar.success("Custom AOI active")

if aoi == "Demo flood zone":
    st.sidebar.success("Demo AOI selected")
else:
    st.sidebar.info("Draw a polygon or rectangle on the map to define a custom AOI.")

st.markdown(f"### Selected event: {event}")
st.caption(
    f"Analysis period: {before_date} → {after_date} | "
    f"Priority: {data['priority']} | "
    f"Confidence: {data['confidence']}%"
)
if st.session_state.get("analysis_run", False):
    st.caption("Analysis status: Complete | Source: Demo satellite/GIS evidence")
else:
    st.caption("Analysis status: Ready | Source: Demo satellite/GIS evidence")
st.markdown("### Event information")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.write(f"**Event:** {event}")
    st.write(f"**Priority:** {data['priority']}")

with info_col2:
    st.write(f"**Latitude:** {data['location'][0]}")
    st.write(f"**Longitude:** {data['location'][1]}")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Flood impact map")

    flood_map = folium.Map(
    location=data["location"],
    zoom_start=11,
    tiles="OpenStreetMap"
)
    flood_layer = folium.FeatureGroup(name="Flood Extent")
    building_layer = folium.FeatureGroup(name="Affected Buildings")
    road_layer = folium.FeatureGroup(name="Roads at Risk")
    Draw(
    export=True,
    position="topleft",
    draw_options={
        "polyline": False,
        "polygon": True,
        "rectangle": True,
        "circle": False,
        "marker": False,
        "circlemarker": False
    },
    edit_options={
        "edit": True,
        "remove": True
    }
    ).add_to(flood_map)

    flood_layer.add_to(flood_map)
    building_layer.add_to(flood_map)
    road_layer.add_to(flood_map)

    folium.Marker(
    data["location"],
    tooltip=f"{event} flood area"
).add_to(flood_map)

  

    folium.Polygon(
       locations=data["flood_zone"],
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.35,
        tooltip="Demo flood-affected zone"
    ).add_to(flood_layer)
    for point in data["buildings_points"]:

        folium.CircleMarker(
        location=point,
        radius=5,
        tooltip="Affected building"
    ).add_to(building_layer)

    road_points = [
    data["flood_zone"][0],
    data["flood_zone"][2]
    ]

    folium.PolyLine(
        locations=road_points,
        weight=5,
        tooltip="Road at risk"
    ).add_to(road_layer)
    folium.LayerControl(collapsed=False).add_to(flood_map)
    
    map_data = st_folium(
    flood_map,
    width=700,
    height=500
)

    if map_data and map_data.get("last_active_drawing"):
        st.session_state.drawn_aoi = map_data["last_active_drawing"]
        st.success("AOI selected successfully.")

    drawn_aoi = st.session_state.drawn_aoi

    if drawn_aoi:
        aoi_area = calculate_aoi_area(drawn_aoi)

        st.success("Custom AOI selected")
        st.metric("Selected AOI Area", f"{aoi_area:.2f} km²")
        st.caption("Demo impact estimates are based on the selected AOI area.")
    else:
        st.info("No custom AOI selected. Draw a polygon or rectangle on the map.")

    if st.session_state.drawn_aoi:
        aoi_geometry = st.session_state.drawn_aoi["geometry"]
    else:
        aoi_geometry = {
            "type": "Polygon",
            "coordinates": [
                [
                [point[1], point[0]]
                for point in data["flood_zone"]
                ]
        ]
    }

    geojson_data = {
        "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "event": event,
                "priority": data["priority"],
                "confidence": data["confidence"]
            },
            "geometry": aoi_geometry
        }
    ]
}


    st.download_button(
        "Download Flood Zone GeoJSON",
        data=json.dumps(geojson_data, indent=2),
        file_name=f"{event.replace(' ', '_')}_flood_zone.geojson",
        mime="application/geo+json"
    )
    st.markdown("### Before vs After Imagery")

    before_col, after_col = st.columns(2)

    with before_col:
        st.markdown("**Before Flood**")
        st.image(
            "https://placehold.co/600x350?text=Pre-Flood+Satellite+Image",
        use_container_width=True
        )

    with after_col:
        st.markdown("**After Flood**")
        st.image(
    "https://placehold.co/600x350?text=Post-Flood+Satellite+Image",
    use_container_width=True
)

        st.markdown("### Imagery Comparison")

    comparison = st.slider(
        "Before ↔ After comparison",
        min_value=0,
        max_value=100,
        value=50,
        help="Move the slider to compare pre-flood and post-flood imagery."
)

    st.caption(
        f"Comparison position: {comparison}%"
    )
with col2:
    st.markdown("### Risk summary")
    st.metric("Affected buildings", data["buildings"])
    st.metric("Roads at risk", f'{data["roads"]} km')
    st.metric("Population affected", f'{data["population"]:,}')
    st.metric("Flood area", f'{data["flood_area"]} km²')
    st.metric("Model confidence", f'{data["confidence"]}%')
    st.progress(
    data["confidence"] / 100,
    text=f"Flood detection confidence: {data['confidence']}%"
)
    st.metric("Priority", data["priority"])
    impact_data = {
    "Category": ["Buildings", "Roads", "Population"],
    "Value": [data["buildings"], data["roads"], data["population"]]
}

    chart = px.bar(
    impact_data,
    x="Category",
    y="Value",
    title="Estimated Flood Impact"
    )

    st.plotly_chart(chart, use_container_width=True)
    st.markdown("### Priority zones")

    if data["priority"] == "High":
        zone_a_score = 92
    elif data["priority"] == "Medium":
        zone_a_score = 72
    else:
        zone_a_score = 48

    zone_data = {
    "Rank": [1, 2, 3],
    "Zone": ["Zone A", "Zone B", "Zone C"],
    "Priority": [
        data["priority"],
        "Medium",
        "Low"
    ],
    "Risk Score": [
        zone_a_score,
        max(zone_a_score - 24, 0),
        max(zone_a_score - 51, 0)
    ],
    "Status": [
        "Immediate attention",
        "Monitor",
        "Low risk"
    ]
}

    st.dataframe(
    zone_data,
    use_container_width=True,
    hide_index=True
    )
    selected_zone = st.selectbox(
    "View zone details",
    ["Zone A", "Zone B", "Zone C"]
    )

    zone_details = {
    "Zone A": {"risk": zone_a_score, "status": "Immediate attention"},
    "Zone B": {"risk": 68, "status": "Monitor"},
    "Zone C": {"risk": 41, "status": "Low risk"}
    }

    selected = zone_details[selected_zone]

    st.info(
    f"**{selected_zone}** — Risk Score: **{selected['risk']}** | "
    f"Status: **{selected['status']}**"
    )
    st.markdown("### 🤖 AI Incident Assistant")
    st.caption("AI-generated briefing based on mapped flood evidence")

    st.markdown("#### Situation")
    st.markdown(
    f"**Incident Summary**  \n"
    f"{event} has been classified as **{data['priority']} priority**. "
    f"An estimated **{data['population']:,} people** and "
    f"**{data['buildings']} buildings** may be affected, with "
    f"approximately **{data['roads']} km of roads** at risk."
    )
    st.markdown("#### Risk Assessment")

    if data["priority"] == "High":
        risk_message = (
            "The affected area shows significant potential impact. "
            "Immediate assessment of high-risk zones is recommended."
        )
    elif data["priority"] == "Medium":
        risk_message = (
            "The affected area shows moderate potential impact. "
            "Priority zones should be monitored and assessed."
        )
    else:
        risk_message = (
            "The affected area shows relatively low potential impact. "
            "Continued monitoring is recommended."
        )

    st.write(risk_message)
    st.markdown("#### Recommended Actions")

    st.write("1. Assess buildings located inside the mapped flood zone.")
    st.write("2. Inspect roads identified as being at risk.")
    st.write("3. Prioritize high-impact zones for emergency assessment.")
    st.write("4. Verify satellite and GIS evidence before taking action.")

    st.caption(
    f"AI briefing based on mapped evidence | "
    f"Model confidence: {data['confidence']}%"
    )
    st.markdown("---")

