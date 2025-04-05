from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Conectar con MongoDB
client = MongoClient("mongodb+srv://simgt:jj9lP1lVwcIQHklu@simgt.25nvu.mongodb.net/simgt")
db = client["simgt"]
collection = db["Conteo"]
traffic_1_collection = db["traffic_1"]
traffic_2_collection = db["traffic_2"]

# Función para predecir el tráfico basado en los datos de los sensores
def predict_traffic(ir1, ir2, ir3, ir4, ir5, ir6):
    # Lógica simple para predecir tráfico: si más de 3 sensores están activos, el tráfico es alto.
    active_sensors = sum([ir1, ir2, ir3, ir4, ir5, ir6])
    print(f"Total de sensores activos: {active_sensors}")  # Agregar log para depuración
    
    if active_sensors >= 4:
        return "Alta"
    elif active_sensors == 3:
        return "Moderada"
    else:
        return "Baja"

# Ruta para recibir datos del ESP32
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    try:
        # Extraer datos
        ir1 = data.get("ir1")
        ir2 = data.get("ir2")
        ir3 = data.get("ir3")
        ir4 = data.get("ir4")
        ir5 = data.get("ir5")
        ir6 = data.get("ir6")
        latitud = float(data.get("Latitud", 0))  # Convertir a float
        longitud = float(data.get("Longitud", 0))  # Convertir a float

        # Verificar que las coordenadas sean válidas
        if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
            return jsonify({"error": "Coordenadas fuera de rango"}), 400

        # Imprimir los datos recibidos para depuración
        print(f"Datos recibidos: {data}")

        # Crear documento para MongoDB
        new_entry = {
            "ir1": ir1, "ir2": ir2, "ir3": ir3, "ir4": ir4,
            "ir5": ir5, "ir6": ir6, "Latitud": latitud, 
            "Longitud": longitud, "timestamp": datetime.now(timezone.utc)
        }

        # Verificar si la colección está disponible
        if collection is None:
            return jsonify({"error": "La colección no está disponible"}), 500

        # Guardar en la base de datos
        result = collection.insert_one(new_entry)
        if result.acknowledged:
            return jsonify({"message": "Datos guardados correctamente"}), 200
        else:
            return jsonify({"error": "No se pudo guardar los datos, inserción fallida"}), 500
    except Exception as e:
        return jsonify({"error": f"Error al recibir los datos: {str(e)}"}), 500

# Ruta para obtener el último documento almacenado y predecir el tráfico
@app.route('/dataob', methods=['GET'])
def get_data():
    try:
        # Obtener el último documento de la base de datos
        last_entry = collection.find().sort("timestamp", -1).limit(1)
        
        # Si no hay datos, devolver un error
        if not last_entry:
            return jsonify({"error": "No hay datos disponibles"}), 404
        
        last_entry = list(last_entry)[0]  # Convertir el cursor en lista y obtener el primer documento

        # Extraer los valores de los sensores del último documento
        ir1 = last_entry.get("ir1")
        ir2 = last_entry.get("ir2")
        ir3 = last_entry.get("ir3")
        ir4 = last_entry.get("ir4")
        ir5 = last_entry.get("ir5")
        ir6 = last_entry.get("ir6")

        print(f"Datos del último documento: {ir1}, {ir2}, {ir3}, {ir4}, {ir5}, {ir6}")

        # Obtener la predicción de tráfico
        traffic_prediction = predict_traffic(ir1, ir2, ir3, ir4, ir5, ir6)
        print(f"Predicción de tráfico: {traffic_prediction}")  # Log de la predicción
        
        # Añadir la predicción al documento
        last_entry['traffic_prediction'] = traffic_prediction
        last_entry['_id'] = str(last_entry['_id'])

        return jsonify(last_entry), 200  # Devolver el último documento con la predicción incluida

    except Exception as e:
        return jsonify({"error": f"Error al obtener los datos: {str(e)}"}), 500

@app.route('/traffic_analysis', methods=['GET'])
def traffic_analysis():
    try:
        # Obtener los datos de las colecciones traffic_1 y traffic_2
        traffic_data_1 = list(traffic_1_collection.find({"signal_status": "Red"}, {"_id": 0, "timestamp": 1, "signal_status": 1, "vehicle_count_cars": 1}))
        traffic_data_2 = list(traffic_2_collection.find({"signal_status": "Red"}, {"_id": 0, "timestamp": 1, "signal_status": 1, "vehicle_count_cars": 1}))

        # Unir ambos conjuntos de datos
        traffic_data = traffic_data_1 + traffic_data_2

        # Procesar los datos: convertir timestamp a timestamp Unix y extraer los datos relevantes
        timestamps = []
        vehicle_counts = []

        for entry in traffic_data:
            timestamp = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S").timestamp()  # Convertir timestamp a Unix
            timestamps.append(timestamp)
            vehicle_counts.append(entry['vehicle_count_cars'])

        # Clasificación de tráfico (Bajo, Moderado, Alto)
        traffic_level = {"Bajo": 0, "Moderado": 0, "Alto": 0}
        for count in vehicle_counts:
            if count < 100:
                traffic_level["Bajo"] += 1
            elif 100 <= count < 300:
                traffic_level["Moderado"] += 1
            else:
                traffic_level["Alto"] += 1

        # Devolver los datos para la gráfica
        return jsonify({
            "timestamps": timestamps,
            "vehicle_counts": vehicle_counts,
            "traffic_level": traffic_level
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Iniciar el servidor en el puerto 3002
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, debug=True)
