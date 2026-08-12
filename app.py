from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import math

app = Flask(__name__)
CORS(app)

# Fórmula de Haversine para la distancia real
def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0 # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Función que consume la API en vivo filtrando solo por Honduras
def obtener_api_honduras():
    overpass_url = "http://overpass-api.de/api/interpreter"
    # Consulta a la base de datos: "Dame todo lo que sea policía dentro del área de Honduras"
    query = """
    [out:json];
    area["name"="Honduras"]->.searchArea;
    node["amenity"="police"](area.searchArea);
    out center;
    """
    try:
        response = requests.post(overpass_url, data={'data': query})
        data = response.json()
        estaciones = []
        for element in data.get('elements', []):
            # Si la posta no tiene nombre en la base de datos, le asignamos uno genérico
            nombre = element.get('tags', {}).get('name', 'Posta Policial (Honduras)')
            estaciones.append({
                "nombre": nombre,
                "lat": element['lat'],
                "lon": element['lon']
            })
        return estaciones
    except Exception as e:
        print("Error consumiendo la API externa:", e)
        return None

@app.route('/estaciones', methods=['GET'])
def buscar_cercanas():
    try:
        lat_usuario = float(request.args.get('lat'))
        lon_usuario = float(request.args.get('lon'))
        limite = int(request.args.get('limite', 3))
        
        # 1. Intentamos consumir la API en vivo de Honduras
        estaciones = obtener_api_honduras()
        
        # 2. Si la API falla o tarda, usamos el JSON que te pide la rúbrica
        if not estaciones or len(estaciones) == 0:
            with open('estaciones.json', 'r', encoding='utf-8') as file:
                estaciones = json.load(file)
                
        # 3. Calculamos distancias exactas hacia tu coordenada
        for estacion in estaciones:
            dist = calcular_distancia(lat_usuario, lon_usuario, estacion['lat'], estacion['lon'])
            estacion['distancia_km'] = round(dist, 2)
            
        # 4. Ordenar y devolver solo las más cercanas
        estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia_km'])
        return jsonify(estaciones_ordenadas[:limite])
        
    except Exception as e:
        return jsonify({"error": "Por favor envía coordenadas válidas."}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
