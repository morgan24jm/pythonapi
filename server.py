from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Conectar con MongoDB
client = MongoClient("mongodb+srv://simgt:jj9lP1lVwcIQHklu@simgt.25nvu.mongodb.net/simgt")
db = client["simgt"]
collection = db["Conteo"]

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

        # Crear documento para MongoDB
        new_entry = {
            "ir1": ir1, "ir2": ir2, "ir3": ir3, "ir4": ir4,
            "ir5": ir5, "ir6": ir6, "Latitud": latitud, 
            "Longitud": longitud, "timestamp": datetime.utcnow()
        }

        # Guardar en la base de datos
        collection.insert_one(new_entry)
        return jsonify({"message": "Datos guardados correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para obtener todos los datos almacenados
@app.route('/dataob', methods=['GET'])
def get_data():
    try:
        data = list(collection.find({}, {"_id": 0}))  # Excluir _id de la respuesta
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Iniciar el servidor en el puerto 3000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
