import threading

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os
import time

app=Flask(__name__)


@app.route('/')
def index():
    url='https://mem-hub.ru/'
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
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
    #print("Уникальные ссылки пагинации:")
    for i, url in enumerate(sorted_urls, 1):
        #print(f"{i}. {url}")
    
        page_response = request.get(url, headers=headers) #cкачиваем страницу HTML структуру

        if page_response.status_code==200:
            soup=BeautifulSoup(page_response.text, 'html.parser') #Скачиную страницу парсим спомощью html.парсера

        # Ищем все теги <source> с type="video/mp4" или другими видеоформатами
            video_tags=soup.find_all('video')

            for video in video_tags:
                sources =video.find_all('source')
                for source in sources:
                    src=source.get('src')
                    if src:
                        full_url=urljoin(base_url, src)
    return render_template('index.html', data=full_url)
       
        

if __name__=="__main__":
    app.run(debug=True, port=5003)
