from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import math

app = Flask(__name__)
CORS(app)

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def obtener_api_honduras():
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = '''
    [out:json];
    area["name"="Honduras"]->.searchArea;
    node["amenity"="police"](area.searchArea);
    out center;
    '''
    try:
        response = requests.post(overpass_url, data={'data': query})
        data = response.json()
        estaciones = []
        for element in data.get('elements', []):
            nombre = element.get('tags', {}).get('name', 'Posta Policial (Honduras)')
            estaciones.append({
                "nombre": nombre,
                "lat": element['lat'],
                "lon": element['lon']
            })
        return estaciones
    except:
        return None

@app.route('/estaciones', methods=['GET'])
def buscar_cercanas():
    try:
        lat_usuario = float(request.args.get('lat'))
        lon_usuario = float(request.args.get('lon'))
        limite = int(request.args.get('limite', 3))
        
        estaciones = obtener_api_honduras()
        
        if not estaciones or len(estaciones) == 0:
            with open('estaciones.json', 'r', encoding='utf-8') as file:
                estaciones = json.load(file)
                
        for estacion in estaciones:
            dist = calcular_distancia(lat_usuario, lon_usuario, estacion['lat'], estacion['lon'])
            estacion['distancia_km'] = round(dist, 2)
            
        estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia_km'])
        return jsonify(estaciones_ordenadas[:limite])
        
    except Exception as e:
        return jsonify({"error": "Por favor envía coordenadas válidas."}), 400

# ---- NUEVA RUTA PARA EL MENÚ DESPLEGABLE ----
@app.route('/todas', methods=['GET'])
def obtener_todas():
    try:
        with open('estaciones.json', 'r', encoding='utf-8') as file:
            estaciones = json.load(file)
        return jsonify(estaciones)
    except Exception as e:
        return jsonify({"error": "Error cargando la base de datos interna."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
