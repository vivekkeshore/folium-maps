import json
import re

import folium
from folium import FeatureGroup
from folium.plugins import HeatMap, TimestampedGeoJson, AntPath
from static_html import title_html, countries_list_html

from iran_conflict_strike_data import iran_strike_events, retaliation_events


# Load the correct political border of India from the provided GeoJSON file and add it to the map.
def load_india_geojson(map_obj: folium.Map, geojson_path: str):
    with open(geojson_path, "r") as f:
        geo_json_data = json.load(f)
    folium.GeoJson(
        geo_json_data,
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#FF6B35",
            "weight": 3,
        },
        name="India Political Map",
    ).add_to(map_obj)


def group_events_by_location(
    events: list[dict],
) -> list[tuple[float, float, list[dict]]]:
    """Group events sharing the same coordinates while preserving input order."""
    grouped: dict[tuple[float, float], list[dict]] = {}
    order: list[tuple[float, float]] = []
    for event in events:
        key = (round(event["lat"], 6), round(event["lon"], 6))
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(event)
    return [(lat, lon, grouped[(lat, lon)]) for lat, lon in order]


def build_grouped_popup(events: list[dict], color: str, group_name: str) -> str:
    """Build one popup that lists all same-location events."""
    if len(events) == 1:
        event = events[0]
        return (
            f'<b style="color:{color}">{group_name}</b><br><b>{event["name"]}</b>'
            f'<br>Date: {event["date"]}<br><br>{event["desc"]}'
        )

    lines = [
        f'<b style="color:{color}">{group_name} ({len(events)} events at this location)</b>'
    ]
    for idx, event in enumerate(events, start=1):
        lines.append(
            f'<br><br><b>{idx}. {event["name"]}</b><br>Date: {event["date"]}<br>{event["desc"]}'
        )
    return "".join(lines)


def add_strike_markers(
    map_obj: folium.Map, events: list[dict], color: str, group_name: str
):
    """Adds markers for strike events with specified color and icon."""
    feature_group = FeatureGroup(name=group_name)
    for lat, lon, grouped_events in group_events_by_location(events):
        icon_name = (
            "sailboat"
            if any(
                "dena" in event["name"].lower() or "torpedo" in event["name"].lower()
                for event in grouped_events
            )
            else "burst"
        )
        tooltip = (
            grouped_events[0]["name"]
            if len(grouped_events) == 1
            else f"{grouped_events[0]['name']} (+{len(grouped_events) - 1} more)"
        )
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(
                build_grouped_popup(grouped_events, color, group_name),
                max_width=420,
            ),
            tooltip=tooltip,
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
        ).add_to(feature_group)

    # Add feature group to map.
    feature_group.add_to(map_obj)


def add_heatmaps(
    map_obj: folium.Map, events: list[dict], color_scheme: dict, group_name: str
):
    """Adds a heatmap layer for the given events with specified color scheme."""
    HeatMap(
        [[event["lat"], event["lon"], 1] for event in events],
        name=group_name,
        radius=38,
        blur=35,
        min_opacity=0.4,
        gradient=color_scheme,
    ).add_to(map_obj)


def resolve_strike_launch(event: dict) -> tuple[list[float], str]:
    """Select launch points for Israel/US strike events."""
    if "torpedo" in event["name"].lower() or "dena" in event["name"].lower():
        return [4.064516, 80.508032], "US Submarine (Indian Ocean)"
    if event["lat"] > 30:
        return [31.2089, 35.0114], "Nevatim Air Base, Israel"
    if "navy" in event["name"].lower() or "port" in event["name"].lower():
        return [26.0, 56.0], "US Carrier (Persian Gulf)"
    return [25.117, 51.315], "Al Udeid Air Base, Qatar"


def resolve_retaliation_launch(event: dict) -> tuple[list[float], str]:
    """Select launch points for Iranian retaliation events."""
    kermanshah_launch = [34.3277, 47.0778]
    khorramabad_launch = [33.487, 48.355]
    shiraz_launch = [29.5918, 52.5836]
    konarak_launch = [25.3667, 60.4]
    bandar_abbas_launch = [27.18, 56.27]

    if "Israel" in event["name"]:
        if "Tel Aviv" in event["name"] or "Beit Shemesh" in event["name"]:
            return kermanshah_launch, "Kermanshah Missile Site"
        return khorramabad_launch, "Khorramabad Missile Site"
    if "Baghdad" in event["name"] or "Iraq" in event["name"]:
        return kermanshah_launch, "Kermanshah Missile Site"
    if "Saudi" in event["name"] or "Riyadh" in event["name"]:
        return shiraz_launch, "Shiraz Missile Base"
    if "UAE" in event["name"] or "Dubai" in event["name"]:
        return konarak_launch, "Konarak Air Base"
    return bandar_abbas_launch, "Bandar Abbas Missile Site"


def add_antpaths(
    map_obj: folium.Map,
    events: list[dict],
    color: str,
    group_name: str,
    launch_resolver,
    marker_color: str,
    marker_icon: str,
):
    """Adds AntPath trails from computed launch points to strike locations."""
    antpaths_group = FeatureGroup(name=group_name)
    for event in events:
        launch_point, launch_name = launch_resolver(event)
        AntPath(
            locations=[launch_point, [event["lat"], event["lon"]]],
            color=color,
            weight=4,
            opacity=0.9,
            delay=800,
            dash_array=[10, 20],
            popup=f"{group_name} Path from {launch_name} -> {event['name']} ({event['date']})",
        ).add_to(antpaths_group)
        folium.Marker(
            launch_point,
            popup=folium.Popup(
                f'<b style="color:{marker_color}">{launch_name}</b><br>Launch Site for {event["name"]}',
                max_width=300,
            ),
            tooltip=launch_name,
            icon=folium.Icon(color=marker_color, icon=marker_icon, prefix="fa"),
        ).add_to(antpaths_group)
    antpaths_group.add_to(map_obj)


def parse_event_dates(raw_date: str) -> list[str]:
    """Parse raw date text into normalized YYYY-MM-DD values."""
    tokens = [
        t.strip() for t in re.split(r"\s*(?:&|,|\band\b)\s*", raw_date) if t.strip()
    ]
    parsed_dates = []
    seen = set()
    current_year = "2026"
    current_month = None

    for token in tokens:
        full_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", token)
        month_day_match = re.fullmatch(r"(\d{2})-(\d{2})", token)
        day_match = re.fullmatch(r"(\d{2})", token)

        if full_match:
            year, month, day = full_match.groups()
            current_year, current_month = year, month
            normalized = f"{year}-{month}-{day}"
        elif month_day_match:
            month, day = month_day_match.groups()
            current_month = month
            normalized = f"{current_year}-{month}-{day}"
        elif day_match and current_month is not None:
            day = day_match.group(1)
            normalized = f"{current_year}-{current_month}-{day}"
        else:
            continue

        if normalized not in seen:
            seen.add(normalized)
            parsed_dates.append(normalized)

    return parsed_dates


def expand_event_dates(raw_date: str) -> list[str]:
    """Return TimestampedGeoJson-compatible timestamps for event dates."""
    return [f"{date_part}T12:00:00" for date_part in parse_event_dates(raw_date)]


def build_animation_feature(
    event: dict,
    timestamps: list[str],
    popup_title: str,
    popup_color: str,
    fill_color: str,
    radius: int,
) -> dict:
    """Build one GeoJSON point feature for timeline animation."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [event["lon"], event["lat"]]},
        "properties": {
            "times": timestamps,
            "popup": f'<b style="color:{popup_color}">{popup_title}</b><br><b>{event["name"]}</b><br>Date: {event["date"]}<br><br>{event["desc"]}',
            "icon": "circle",
            "iconstyle": {
                "fillColor": fill_color,
                "fillOpacity": 0.95,
                "color": "#000",
                "weight": 3.5,
                "radius": radius,
            },
        },
    }


def strike_animation_style(event: dict) -> tuple[str, int]:
    """Highlight torpedo/dena strike events with stronger style."""
    is_torpedo = "dena" in event["name"].lower() or "torpedo" in event["name"].lower()
    if is_torpedo:
        return "#ff5722", 16
    return "#d32f2f", 11


def retaliation_animation_style(event: dict) -> tuple[str, int]:
    """Standard style for retaliation timeline points."""
    return "#1976d2", 11


def _add_animation_features(
    events: list[dict],
    popup_title: str,
    popup_color: str,
    style_resolver,
) -> list[dict]:
    """Convert event records into timeline-ready GeoJSON features."""
    features = []
    for event in events:
        fill_color, radius = style_resolver(event)
        timestamps = expand_event_dates(event["date"])
        if not timestamps:
            continue
        features.append(
            build_animation_feature(
                event,
                timestamps,
                popup_title,
                popup_color,
                fill_color,
                radius,
            )
        )
    return features


def add_animation_features(map_obj: folium.Map):
    """Adds timeline animation features to the map."""
    # Timed paths + circles in slider for key events (e.g. torpedo strike, major retaliations).
    animation_features = []
    animation_features.extend(
        _add_animation_features(
            iran_strike_events,
            popup_title="🟥 ISRAEL/US STRIKE",
            popup_color="#d32f2f",
            style_resolver=strike_animation_style,
        )
    )
    animation_features.extend(
        _add_animation_features(
            retaliation_events,
            popup_title="🟦 IRANIAN RETALIATION",
            popup_color="#1976d2",
            style_resolver=retaliation_animation_style,
        )
    )
    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": animation_features},
        period="P1D",
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=4,
        loop_button=True,
        date_options="YYYY-MM-DD",
        time_slider_drag_update=True,
        transition_time=800,
    ).add_to(map_obj)


def main():
    conflict_map = folium.Map(
        location=[22.0, 55.0],
        zoom_start=4,
        tiles="CartoDB positron",
        control_scale=True,
        font_size="16px",
    )

    # Load correct India border and add to map.
    load_india_geojson(conflict_map, "india.geojson")

    # Add strike markers, heatmaps, AntPaths, and timeline animation features.
    add_strike_markers(
        conflict_map,
        iran_strike_events,
        color="red",
        group_name="🟥 Israel/US Strikes on Iran (incl. Torpedo Strike)",
    )

    add_strike_markers(
        conflict_map,
        retaliation_events,
        color="blue",
        group_name="🟦 Iranian Retaliation",
    )

    # Heatmaps with custom color gradients for strike and retaliation events.
    add_heatmaps(
        conflict_map,
        iran_strike_events,
        color_scheme={0.3: "#ffeb3b", 0.6: "#ff9800", 1: "#d32f2f"},
        group_name="🔥 Heatmap: Israel/US Strikes on Iran",
    )
    add_heatmaps(
        conflict_map,
        retaliation_events,
        color_scheme={0.3: "#bbdefb", 0.6: "#2196f3", 1: "#1976d2"},
        group_name="🔥 Heatmap: Iranian Retaliation",
    )

    # AntPaths from launch points to strike locations.
    add_antpaths(
        conflict_map,
        iran_strike_events,
        color="red",
        group_name="🟥 AntPaths: USA/Israel Strikes on Iran",
        launch_resolver=resolve_strike_launch,
        marker_color="green",
        marker_icon="shuttle-space",
    )

    add_antpaths(
        conflict_map,
        retaliation_events,
        color="blue",
        group_name="🟦 AntPaths: Iranian Retaliation",
        launch_resolver=resolve_retaliation_launch,
        marker_color="orange",
        marker_icon="rocket",
    )

    # Re-add timeline slider layer.
    add_animation_features(conflict_map)

    conflict_map.get_root().html.add_child(folium.Element(countries_list_html))
    conflict_map.get_root().html.add_child(folium.Element(title_html))
    folium.LayerControl(collapsed=False).add_to(conflict_map)

    # Save the map to an HTML file.
    conflict_map.save("iran_conflict_map_complete.html")


if __name__ == "__main__":
    main()
