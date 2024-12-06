# app.py
from flask import Flask, jsonify #импорт необходимых модулей

app = Flask(__name__) #создание экземпляра приложения фласк

port = 5001  #порт 1,2,3 на котором будет запускаться приложение 

@app.route('/health', methods=['GET']) #Определяем маршрут для проверки состояния
def health(): #определение функции для маршрута 
    return jsonify({"status": "healthy"}), 200 #Функция возвращает JSON-ответ с ключом status и значением healthy, 
    #а также HTTP-статус 200, что означает успешный запрос

@app.route('/process', methods=['GET']) #Определяем маршрут для обработки
def process():
    instance_id = f"Instance running on port {port}" #содержит информацию о том, что экземпляр приложения работает на заданном порту.
    return jsonify({"instance_id": instance_id}), 200 #Функция возвращает JSON-ответ с ключом instance_id, содержащим информацию о порте, и статус 200.

if __name__ == '__main__': #выполняется ли скрипт как основная программа. Если это так, то выполняется следующий код.
    app.run(port=port) #запускаем приложение Flask на порту, указанном в переменной port.
