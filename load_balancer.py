from flask import Flask, request, jsonify, render_template, redirect, url_for
import requests
import time

app = Flask(__name__)

instances = [] #список, который будет хранить информацию о доступных экземплярах приложений
round_robin_index = 0 #используется для реализации алгоритма кругового распределения запросов между экземплярами

@app.route('/health') # проверка состояни]я
def health(): #маршрут для проверки состояния
    return 'status: healthy'

@app.route('/process', methods=['GET', 'POST']) # перенаправка запросов на активный инстанс
def process(): #маршрут /process возвращает текст, указывающий, что экземпляр работает
    return 'instance running'

def check_health(): #Эта функция будет постоянно проверять состояние всех экземпляров в списке instances.
    global instances
    while True:
        for instance in instances: #Мы проходим по каждому экземпляру в списке instances.
            try:
                response = requests.get(f'http://{instance["ip"]}:{instance["port"]}/health', timeout=5)
                #Мы отправляем GET-запрос на маршрут /health каждого экземпляра, используя его IP и порт. Устанавливаем таймаут в 5 секунд.
                if response.status_code != 200: #Если статус-код ответа не 200, мы помечаем экземпляр как "Недоступен", иначе — как "Доступен".
                    instance["status"] = "Недоступен"
                else:
                    instance["status"] = "Доступен"
            except requests.exceptions.RequestException: #Если возникает ошибка при выполнении запроса, мы также помечаем экземпляр как "Недоступен".
                instance["status"] = "Недоступен"
        time.sleep(5) #делаем паузу на 5 секунд перед следующей итерацией проверки состояния экземпляров

# Чтение портов из файла
with open("ports.txt", 'r') as f: #Открываем файл ports.txt для чтения и считываем все строки, которые будут содержать порты экземпляров
    ports = f.read().splitlines()
    for port in ports: #Для каждого порта, который является числом, мы добавляем новый экземпляр в список instances с IP-адресом 127.0.0.1 и статусом по умолчанию
        if port.strip().isdigit():
            instances.append({"ip": "127.0.0.1", "port": int(port.strip()), "status": ""})

@app.route('/health') #Этот маршрут возвращает JSON-ответ с информацией о доступных экземплярах
def health_instances():
    active_instances = [instance for instance in instances if instance['status'] == 'Доступен']
    return jsonify(instances=active_instances)

@app.route('/process', methods=['GET', 'POST']) #Здесь мы собираем список доступных экземпляров для обработки запросов.
    global round_robin_index
    active_instances = [instance for instance in instances if instance['status'] == 'Доступен']

    if len(active_instances) == 0: #Если нет доступных экземпляров, возвращаем ошибку 503
        return jsonify(error="Нет доступных приложений"), 503

    instance = active_instances[round_robin_index] #Мы выбираем экземпляр по круговому принципу и обновляем индекс для следующего запроса
    round_robin_index = (round_robin_index + 1) % len(active_instances)

    response = requests.get(f'http://{instance["ip"]}:{instance["port"]}/process') 
    #Мы отправляем GET-запрос на маршрут /process выбранного экземпляра и возвращаем его JSON-ответ
    return jsonify(response.json())

@app.route('/') #Этот маршрут рендерит HTML-шаблон index.html, передавая список экземпляров
def index():
    return render_template('index.html', instances=instances)

@app.route('/add_instance', methods=['POST']) #Мы получаем IP и порт из формы, добавляем новый экземпляр в список и записываем его в файл ports.txt.
def add_instance():
    ip = request.form['ip']
    port = int(request.form['port'])
    instances.append({"ip": ip, "port": port, "status": ''})
    with open('ports.txt', 'a') as f: #добавляем порт в файл и перенаправляем пользователя на главную страницу. 'a'-режим добавления
        # a -если файл существует, новые данные будут добавлены в конец файла, а если нет — файл будет создан
        f.write(f"{port}\n") #f-объект файла с которым мы можем работать в блоке with
    return redirect(url_for('index'))

@app.route('/remove_instance', methods=['POST']) #получаем индекс экземпляра из формы и удаляем его из списка, если индекс корректен
def remove_instance():
    index = int(request.form['index']) - 1 #извлекаем значение index из данных формы, отправленных пользователем. 
    #Значение преобразуется в целое число, и мы уменьшаем его на 1, чтобы привести его к индексации списка (так как индексация в Python начинается с 0)
    if 0 <= index < len(instances): # находится ли индекс в допустимом диапазоне. Условие проверяет, что индекс не меньше 0 и меньше длины списка instances
        instances.pop(index) #Метод pop() удаляет элемент из списка и возвращает его

        with open('ports.txt', 'w') as f: #перезаписываем файл ports.txt, чтобы отразить изменения, и перенаправляем на главную страницу
            # 'w'В этом режиме, если файл уже существует, его содержимое будет удалено, и файл будет создан заново
            for instance in instances: #начинает цикл, который проходит по каждому экземпляру в списке instances
                f.write(f"{instance['port']}\n") #Внутри цикла мы записываем порт каждого экземпляра в файл ports.txt. 
                #Используя f-строку, мы форматируем строку так, чтобы она содержала только номер порта, за которым следует символ новой строки (\n). 
                #Это позволяет каждому порту занимать отдельную строку в файле.
    return redirect(url_for('index')) #Функция url_for('index') генерирует URL для маршрута index, что позволяет пользователю вернуться на главную страницу 
                #приложения после того, как изменения были сохранены в файле

@app.route('/<path:path>', methods=['GET', 'POST']) #перехват запросов и перенаправка на доступные инстансы
def catch_all(path):
    global round_robin_index
    active_instances = [instance for instance in instances if instance['status'] == 'Доступен']

    if len(active_instances) == 0: #Если нет доступных экземпляров, возвращаем ошибку 503
        return jsonify(error="Нет доступных приложений"), 503

    instance = active_instances[round_robin_index] #Мы выбираем экземпляр по круговому принципу и обновляем индекс
    round_robin_index = (round_robin_index + 1) % len(active_instances)

    response = requests.request( #Мы отправляем запрос (GET или POST) на выбранный экземпляр, передавая данные, заголовки и куки.
        method=request.method,
        url=f'http://{instance["ip"]}:{instance["port"]}/{path}',
        data=request.data,
        headers=request.headers,
        cookies=request.cookies
    )
    return (response.text, response.status_code, response.headers.items()) #возвращаем текст ответа, статус-код и заголовки.

if __name__ == '__main__':
    app.run(port=5001, debug=True)
