# app.py
from flask import Flask, jsonify

app = Flask(__name__)

port = 5001  #порт 1,2,3

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/process', methods=['GET'])
def process():
    instance_id = f"Instance running on port {port}"
    return jsonify({"instance_id": instance_id}), 200

if __name__ == '__main__':
    app.run(port=port)
