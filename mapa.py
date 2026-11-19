import pandas as pd
import folium

# 1. Cargar los datos
circuitos = pd.read_csv("circuitos.csv").fillna("a definir")
paradas = pd.read_csv("paradas.csv").fillna("a definir")
coords = pd.read_csv("coordenadas.csv")
visitas = pd.read_csv("visitas.csv", dtype=str).fillna("")
asistentes = pd.read_csv("asistentes.csv", dtype=str).fillna("")

# 2. Unir tablas
paradas = paradas.merge(coords, on="localidad", how="left")

faltan = paradas[paradas["lat"].isna()]
if not faltan.empty:
    print("Sin coordenadas:", list(faltan["localidad"]))

paradas = paradas.merge(visitas, on="localidad", how="left")
columnas_visita = ["fecha_visita", "lugar", "referentes", "candidato", "convenio"]
paradas[columnas_visita] = paradas[columnas_visita].fillna("")

# Control de calidad: nombres que no coinciden con ninguna parada
for nombre_tabla, tabla in [("visitas.csv", visitas), ("asistentes.csv", asistentes)]:
    sueltas = set(tabla["localidad"]) - set(paradas["localidad"])
    if sueltas:
        print(f"En {nombre_tabla} hay localidades que no coinciden con ninguna parada:", sueltas)

parana = coords[coords["localidad"] == "Paraná"].iloc[0]
punto_parana = [parana["lat"], parana["lon"]]

# 3. Colores
# Relleno del punto = estado de la visita
ESTADOS = {
    "convenio":      ("#1565c0", "Convenio firmado"),
    "candidato":     ("#2e7d32", "Con candidato"),
    "sin_candidato": ("#c62828", "Visitado, sin candidato"),
    "no_visitado":   ("#9e9e9e", "No visitado"),
}

# Anillo del punto = circuito (colores que NO repiten los de estado)
COLORES_CIRCUITO = {
    1: "#8e24aa",  # violeta
    2: "#ef6c00",  # naranja
    3: "#fdd835",  # amarillo
    4: "#6d4c41",  # marrón
    5: "#f48fb1",  # rosa
    6: "#00bcd4",  # celeste
    7: "#212121",  # negro
}

def calcular_estado(p):
    if p["convenio"].strip().lower() in ("si", "sí"):
        return "convenio"
    if p["candidato"].strip():
        return "candidato"
    if p["fecha_visita"].strip():
        return "sin_candidato"
    return "no_visitado"

def o_pendiente(valor):
    return valor if valor.strip() else "<i>a completar</i>"

def html_asistentes(localidad):
    filas = asistentes[asistentes["localidad"] == localidad]
    if filas.empty:
        return "<i>a completar</i>"

    partes = []
    for institucion, grupo in filas.groupby("institucion", sort=False):
        partes.append(f"<b>{institucion or 'Sin institución informada'}</b>")
        for _, a in grupo.iterrows():
            if a["persona"]:
                linea = a["persona"]
                if a["cargo"]:
                    linea += f" ({a['cargo']})"
                if a["confirmado"].lower() in ("si", "sí"):
                    linea += " ✔ confirmó"
                partes.append(f"&nbsp;&nbsp;• {linea}")
    return "<br>".join(partes)

def anillo(color, tam=10, grosor=3):
    """Circulito con borde de color, para usar en el panel y la barra."""
    return (f'<span style="display:inline-block; width:{tam}px; height:{tam}px; '
            f'border-radius:50%; border:{grosor}px solid {color}; '
            f'margin-right:5px; vertical-align:middle;"></span>')

# 4. Mapa base
# Rectángulo de la provincia: define la vista inicial
PROV_LAT_MIN, PROV_LAT_MAX = -34.1, -30.1
PROV_LON_MIN, PROV_LON_MAX = -60.8, -57.8

mapa = folium.Map(
    location=[-32.0, -59.3],
    zoom_start=7,
    tiles=None,
)
# min_zoom: no deja alejarse más allá de ver la provincia completa
folium.TileLayer("OpenStreetMap", control=False, min_zoom=7).add_to(mapa)

# 5. Un grupo (capa) por circuito
for _, circ in circuitos.iterrows():
    color_circuito = COLORES_CIRCUITO.get(int(circ["circuito"]), "#000000")
    nombre_capa = f"{circ['circuito']}. {circ['nombre']}"
    grupo = folium.FeatureGroup(
        name=f"{anillo(color_circuito)}{nombre_capa}",
        show=False,
    )

    paradas_circ = paradas[paradas["circuito"] == circ["circuito"]].sort_values("orden")

    for _, p in paradas_circ.iterrows():
        estado = calcular_estado(p)
        color, texto_estado = ESTADOS[estado]

        linea_circuito = (f"Circuito <b style='color:{color_circuito}'>"
                          f"{nombre_capa}</b><br>")

        if estado == "no_visitado":
            color_anillo = "#bdbdbd"  # gris claro: sin color de circuito
            texto = (f"<b>{p['localidad']}</b><br>"
                     f"{linea_circuito}"
                     f"Estado: {texto_estado}<br>"
                     f"Permanencia prevista: {p['permanencia']}")
        else:
            color_anillo = color_circuito
            texto = (f"<b>{p['localidad']}</b><br>"
                     f"{linea_circuito}"
                     f"Estado: <b style='color:{color}'>{texto_estado}</b><br>"
                     f"Fecha de visita: {p['fecha_visita']}<br>"
                     f"Lugar: {o_pendiente(p['lugar'])}<br>"
                     f"Referentes: {o_pendiente(p['referentes'])}<br>"
                     f"Candidato Point: {o_pendiente(p['candidato'])}<br>"
                     f"<br><b>Asistentes</b><br>{html_asistentes(p['localidad'])}")

        # Relleno = estado; anillo = circuito (solo en los visitados)
        icono = folium.DivIcon(
            html=f"""<div style="background:{color}; color:white;
                        width:22px; height:22px; border-radius:50%;
                        border:4px solid {color_anillo};
                        box-shadow:0 0 0 2px white, 0 1px 5px rgba(0,0,0,0.5);
                        display:flex; align-items:center; justify-content:center;
                        font:bold 13px sans-serif;">{p['orden']}</div>""",
            icon_size=(30, 30),
            icon_anchor=(15, 15),
        )
        folium.Marker(
            location=[p["lat"], p["lon"]],
            icon=icono,
            tooltip=folium.Tooltip(p["localidad"], permanent=True,
                                   direction="right", offset=(18, 0)),
            popup=folium.Popup(texto, max_width=340),
        ).add_to(grupo)

    grupo.add_to(mapa)

# 6. Paraná: un solo marcador, siempre visible
lineas = [f"{c['circuito']}. {c['nombre']}: sale {c['salida']}, vuelve {c['llegada']}"
          for _, c in circuitos.iterrows()]
texto_parana = "<b>Paraná</b> (salida y llegada)<br>" + "<br>".join(lineas)

folium.Marker(
    punto_parana,
    tooltip=folium.Tooltip("Paraná", permanent=True, direction="right"),
    popup=folium.Popup(texto_parana, max_width=340),
    icon=folium.Icon(color="black", icon="home"),
).add_to(mapa)

# 7. Barra superior (título + leyenda) y estilos
ALTO_BARRA = 50  # en píxeles

estilos = f"""
<style>
html, body {{ margin: 0; height: 100%; }}

#barra {{
    position: fixed; top: 0; left: 0; right: 0;
    height: {ALTO_BARRA}px; box-sizing: border-box;
    display: flex; align-items: center; gap: 28px;
    padding: 0 16px; background: white;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    font-family: sans-serif; z-index: 1000;
    overflow-x: auto; white-space: nowrap;
}}
#barra .titulo {{ font-size: 17px; font-weight: bold; }}
#barra .leyenda {{ display: flex; gap: 16px; font-size: 13px; align-items: center; }}
#barra .nota {{ font-size: 12px; color: #555; }}
#barra .punto {{
    display: inline-block; width: 12px; height: 12px;
    border-radius: 50%; margin-right: 5px; vertical-align: middle;
}}

/* El mapa empieza debajo de la barra, así nada flota sobre él */
.folium-map {{
    position: absolute !important;
    top: {ALTO_BARRA}px !important;
    left: 0 !important;
    width: 100% !important;
    height: calc(100% - {ALTO_BARRA}px) !important;
}}

/* Popups largos: alto máximo con barra de desplazamiento */
.leaflet-popup-content {{
    max-height: 200px;
    overflow-y: auto;
}}
</style>
"""
mapa.get_root().header.add_child(folium.Element(estilos))

items_leyenda = "".join(
    f'<span><span class="punto" style="background:{c};"></span>{t}</span>'
    for c, t in ESTADOS.values()
)
barra = f"""
<div id="barra">
  <span class="titulo">Circuitos por Entre Ríos</span>
  <span class="leyenda">{items_leyenda}</span>
  <span class="nota">Relleno = estado &nbsp;·&nbsp; {anillo('#555', 8, 2)}Anillo = circuito (ver panel)</span>
</div>
"""
mapa.get_root().html.add_child(folium.Element(barra))

# 8. Control de capas, vista inicial y guardar
folium.LayerControl(collapsed=False).add_to(mapa)
mapa.fit_bounds([[PROV_LAT_MIN, PROV_LON_MIN], [PROV_LAT_MAX, PROV_LON_MAX]])
mapa.save("index.html")
print("Listo: abrí index.html")