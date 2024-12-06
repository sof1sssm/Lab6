from flask import Flask, request, jsonify, render_template, redirect, url_for
import requests
import time

app = Flask(__name__)

instances = []
round_robin_index = 0

@app.route('/health') # проверка состояни]я
def health():
    return 'status: healthy'

@app.route('/process', methods=['GET', 'POST']) # перенаправка запросов на активный инстанс
def process():
    return 'instance running'

def check_health():
    global instances
    while True:
        for instance in instances:
            try:
                response = requests.get(f'http://{instance["ip"]}:{instance["port"]}/health', timeout=5)
                if response.status_code != 200:
                    instance["status"] = "Недоступен"
                else:
                    instance["status"] = "Доступен"
            except requests.exceptions.RequestException:
                instance["status"] = "Недоступен"
        time.sleep(5)

# Чтение портов из файла
with open("ports.txt", 'r') as f:
    ports = f.read().splitlines()
    for port in ports:
        if port.strip().isdigit():
            instances.append({"ip": "127.0.0.1", "port": int(port.strip()), "status": ""})

@app.route('/health')
def health_instances():
    active_instances = [instance for instance in instances if instance['status'] == 'Доступен']
    return jsonify(instances=active_instances)

@app.route('/process', methods=['GET', 'POST'])
def process_request():
    global round_robin_index
    active_instances = [instance for instance in instances if instance['status'] == 'Доступен']

    if len(active_instances) == 0:
        return jsonify(error="Нет доступных приложений"), 503

    instance = active_instances[round_robin_index]
    round_robin_index = (round_robin_index + 1) % len(active_instances)

    response = requests.get(f'http://{instance["ip"]}:{instance["port"]}/process')
    return jsonify(response.json())

@app.route('/')
def index():
    return render_template('index.html', instances=instances)

@app.route('/add_instance', methods=['POST'])
def add_instance():
    ip = request.form['ip']
    port = int(request.form['port'])
    instances.append({"ip": ip, "port": port, "status": ''})
    with open('ports.txt', 'a') as f:
        f.write(f"{port}\n")
    return redirect(url_for('index'))

@app.route('/remove_instance', methods=['POST'])
def remove_instance():
    index = int(request.form['index']) - 1
    if 0 <= index < len(instances):
        instances.pop(index)

        with open('ports.txt', 'w') as f:
            for instance in instances:
                f.write(f"{instance['port']}\n")
    return redirect(url_for('index'))

@app.route('/<path:path>', methods=['GET', 'POST']) #перехват запросов и перенаправка на доступные инстансы
def catch_all(path):
    global round_robin_index
    active_instances = [instance for instance in instances if instance['status'] == 'Доступен']

    if len(active_instances) == 0:
        return jsonify(error="Нет доступных приложений"), 503

    instance = active_instances[round_robin_index]
    round_robin_index = (round_robin_index + 1) % len(active_instances)

    response = requests.request(
        method=request.method,
        url=f'http://{instance["ip"]}:{instance["port"]}/{path}',
        data=request.data,
        headers=request.headers,
        cookies=request.cookies
    )
    return (response.text, response.status_code, response.headers.items())

if __name__ == '__main__':
    app.run(port=5001, debug=True)
