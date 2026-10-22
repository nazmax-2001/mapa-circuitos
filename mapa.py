import pandas as pd
import folium

# 1. Cargar los datos
circuitos = pd.read_csv("circuitos.csv").fillna("a definir")
paradas = pd.read_csv("paradas.csv").fillna("a definir")
coords = pd.read_csv("coordenadas.csv")

# 2. Unir paradas con coordenadas (como un JOIN)
paradas = paradas.merge(coords, on="localidad", how="left")

faltan = paradas[paradas["lat"].isna()]
if not faltan.empty:
    print("Sin coordenadas:", list(faltan["localidad"]))

parana = coords[coords["localidad"] == "Paraná"].iloc[0]
punto_parana = [parana["lat"], parana["lon"]]

colores = ["#e6194b", "#3cb44b", "#4363d8", "#f58231",
           "#911eb4", "#008080", "#9a6324"]

# 3. Mapa base
# Límites aproximados de Entre Ríos, con un pequeño margen
LAT_MIN, LAT_MAX = -34.2, -29.9
LON_MIN, LON_MAX = -61.0, -57.6

mapa = folium.Map(
    location=[-32.0, -59.3],
    zoom_start=7,
    tiles=None,
    max_bounds=True,
    min_lat=LAT_MIN, max_lat=LAT_MAX,
    min_lon=LON_MIN, max_lon=LON_MAX,
)
folium.TileLayer("OpenStreetMap", control=False, min_zoom=7).add_to(mapa)

# 4. Un grupo (capa) por circuito
# 4. Un grupo (capa) por circuito
# 4. Un grupo (capa) por circuito
for i, circ in circuitos.iterrows():
    color = colores[i]
    nombre_capa = f"{circ['circuito']}. {circ['nombre']}"
    grupo = folium.FeatureGroup(
    name=f'<span style="color:{color}; font-size:18px;">●</span> {nombre_capa}',
    show=False,
    )

    paradas_circ = paradas[paradas["circuito"] == circ["circuito"]].sort_values("orden")

    # Recorrido con líneas (desactivado: se pidió solo puntos)
    # recorrido = ([punto_parana]
    #              + paradas_circ[["lat", "lon"]].values.tolist()
    #              + [punto_parana])
    # folium.PolyLine(recorrido, color=color, weight=4, opacity=0.8).add_to(grupo)

    for _, p in paradas_circ.iterrows():
        texto = (f"<b>{p['localidad']}</b><br>"
                 f"Circuito {nombre_capa}<br>"
                 f"Permanencia: {p['permanencia']}")
        icono = folium.DivIcon(
            html=f"""<div style="background:{color}; color:white;
                        width:26px; height:26px; border-radius:50%;
                        border:2px solid white; box-shadow:0 1px 4px rgba(0,0,0,0.4);
                        display:flex; align-items:center; justify-content:center;
                        font:bold 14px sans-serif;">{p['orden']}</div>""",
            icon_size=(26, 26),
            icon_anchor=(13, 13),
        )
        folium.Marker(
            location=[p["lat"], p["lon"]],
            icon=icono,
            tooltip=folium.Tooltip(p["localidad"], permanent=True,
                                   direction="right", offset=(14, 0)),
            popup=folium.Popup(texto, max_width=250),
        ).add_to(grupo)

    grupo.add_to(mapa)

# 5. Paraná: un solo marcador, siempre visible
lineas = [f"{c['circuito']}. {c['nombre']}: sale {c['salida']}, vuelve {c['llegada']}"
          for _, c in circuitos.iterrows()]
texto_parana = "<b>Paraná</b> (salida y llegada)<br>" + "<br>".join(lineas)

folium.Marker(
    punto_parana,
    tooltip=folium.Tooltip("Paraná", permanent=True, direction="right"),
    popup=folium.Popup(texto_parana, max_width=320),
    icon=folium.Icon(color="black", icon="home"),
).add_to(mapa)

# 6. Título
titulo = """
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
            z-index: 1000; background: white; padding: 6px 14px;
            border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
            font-family: sans-serif; font-size: 16px; font-weight: bold;">
  Circuitos por Entre Ríos
</div>
"""
mapa.get_root().html.add_child(folium.Element(titulo))

# 7. Control de capas y guardar
folium.LayerControl(collapsed=False).add_to(mapa)
mapa.fit_bounds([[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]])
mapa.save("index.html")
print("Listo: abrí mapa.html")