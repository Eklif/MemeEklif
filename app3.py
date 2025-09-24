from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from collections import defaultdict
from flask import jsonify
from queue import Queue
from threading import Thread
from flask_limiter import Limiter #лимитер на обращения к HTTP Запросам
from flask_limiter.util import get_remote_address

#import eventlet
#eventlet.monkey_patch()


app3=Flask(__name__)
app3.config['SECRET_KEY']='supersecret'
socketio=SocketIO(app3, async_mode='threading') #запуск приложения

#Запускаем лимитер
Limiter_http=Limiter(
    app=app3,
    key_func=get_remote_address,
    default_limits=["200/day", "50/hour"]
)

base_url='https://mem-hub.ru/?sort=count'
headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

url2=[] #список  видео ссылок

video_src=Queue() #Очередь для  ссылок


@socketio.on('connect')#остелживаем подключение клиента
def handle_connect():
    print("Клиетн подключился")
    
def process_queue(): #фунция обработчик очереди запускается в отдельном потоке чтобы не блокировать работу Flask
    while True:
        data2=video_src.get()
        socketio.emit("video_data", data2)#отправляем на html где video_data это событие
        #eventlet.sleep(0)

#Запуск через поток фунции выше
worker_thread=Thread(target=process_queue, daemon=True)
worker_thread.start()
#video_src.join()

#Запускаем функцию обработчик в отдельной потоке временно не работает
#socketio.start_background_task(process_queue())

#Функиция парсинга ссылок
def index1():
    response=requests.get(base_url, headers=headers)
    
    soup=BeautifulSoup(response.text, 'html.parser')

    pagination = soup.find('div', class_='pagination2').find('ul', class_='pagination').find_all('a', class_='page-link')

    unique_urls=set()#создание уникальных ссылок
    for pagination2 in pagination:
        url=pagination2.get('href')
        if url:
            full_url=urljoin(base_url, url)
            unique_urls.add(full_url)
            
    # Функция для сортировки URL

    def sort_key(url):
        if url == base_url or url.endswith('/'):
            return 0
        try:
           return int(url.split('/')[-1])
        except (ValueError, IndexError):
            return float('inf')  # помещаем некорректные URL в конец       

    # Сортируем URL
    sorted_urls = sorted(unique_urls, key=sort_key)

    # Выводим результат
    print("Уникальные ссылки пагинации:")
    for i, url in enumerate(sorted_urls, 1):
        #print(f"{i}. {url}")
    
        page_response = requests.get(url, headers=headers) #cкачиваем страницу HTML структуру

        if page_response.status_code==200:
            soup=BeautifulSoup(page_response.text, 'html.parser') #Скачиную страницу парсим спомощью html.парсера

        #Ищем все теги <source> с type="video/mp4" или другими видеоформатами
            video_tags=soup.find_all('video')
            
            for video in video_tags:
                sources =video.find_all('source')
                for source in sources:
                    src=source.get('src')
                    full_url=urljoin(base_url, src)
                    
                    url2.append(full_url)






#оправляем списков ссылок на hmtl через Json
@app3.route('/', methods=['GET', "POST"])
def index():
    index1()
    data=url2
    return render_template('index.html', data=json.dumps(data))

#Оправка пользователем ссылки на видео на сервер
@app3.route('/send', methods=["POST"])
@Limiter_http.limit("1 per 10 seconds")
def send():
    data = request.get_json()
    array = data['array']
    video_src.put(array)
    print("Массив получен:", array)
    return  jsonify({"message": "Массив отравлен успешно"}) #jsonify функция отарвляющая ответ в формате json на html

#Страничка с видео отправленными на стрим
@app3.route('/send1')
def send_page():
    return render_template('send1.html')

# Обрабочтик срабатывает при привышени лимита
@app3.errorhandler(429)
def ratelimit_error(error):
    return jsonify({"error": "Слишком много запросов! Попробуйте через 10 секунд."}), 429
        
if __name__=="__main__":
   socketio.run(app3, host='0.0.0.0', port=5000, debug=True)

