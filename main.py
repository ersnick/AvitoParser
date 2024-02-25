from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time


# путь к драйверу браузера
driver_path = 'E:\progesNOprogress\pythonProject\AvitoParser\chromedriver.exe'

photo_name = 2


def get_html_page(url):
    s = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=s)

    # Открываем страницу
    driver.get(url)

    # Прокручиваем страницу вниз, чтобы загрузить изображения
    scroll_height = driver.execute_script(
        "return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")

    # Устанавливаем высоту прокрутки
    scroll_step = 1000

    # Проматываем страницу по частям
    for i in range(0, scroll_height, scroll_step):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(1)  # ждем загрузку контента

    # Получаем HTML-код страницы после прокрутки
    return driver.page_source


def parse_html(html_code, df):
    # объявляем глобальную переменную, чтобы она в область видимости входила
    global photo_name

    # достаем нужный нам контейнер
    bs = BeautifulSoup(html_code, "html.parser")
    all_advert = bs.findAll('div', class_='items-items-kAJAg')[0]

    # идем по каждому объявлению
    for advert in all_advert.contents:
        class_name = advert.attrs['class'][0]

        # проверка на рекламный контейнер
        if not class_name.startswith('items-ads') and not class_name.startswith('items-witcher'):

            # profile
            try:
                profile_container = advert.contents[1].contents[0].contents[2].contents[0].contents[0].contents[-1].contents[0].contents[0]
                profile_name = profile_container.contents[-2].text
                profile_rating = profile_container.contents[-1].contents[0].text
                profile_rating = profile_rating.replace(',', '.')
                profile_rating_float = float(profile_rating)

                # проверяем чтобы рейтинг был > 4.5
                if not profile_rating_float > 4.5:
                    continue
            except Exception as e: # рейтинга и имени может не быть
                profile_name = ""
                profile_rating_float = ""


            # name, year, mileage
            info_car_str = advert.contents[1].contents[0].contents[1].contents[1].text
            info_car_list = info_car_str.split(',')
            info_car_list[1] = info_car_list[1].lstrip()

            # пробега может не  быть
            if len(info_car_list) == 3:
                # регулярным выражением убираем лишнее
                mileage = re.sub(r'\s+|\D', '', info_car_list[2])
            else:
                mileage = ""


            # price
            price = advert.contents[1].contents[0].contents[1].contents[2].contents[0].contents[0].text


            # image
            try:
                image_url = advert.contents[1].contents[0].contents[0].contents[0].contents[0].contents[0].contents[0].contents[0].contents[0].contents[0].attrs['src']
                img_data = requests.get(image_url).content

                filename = f'photos/{photo_name}.jpg'

                # Сохраняем изображение
                with open(filename, 'wb') as f:
                    f.write(img_data)

            # нет фото или вместо фото видео
            except Exception as e:
                pass

            # заполняем dataframe
            df.loc[photo_name] = [info_car_list[0], info_car_list[1], mileage, price, profile_name, profile_rating_float]
            photo_name += 1

    df.to_excel('BMW.xlsx', index=False)


if __name__ == "__main__":
    # создаем папку под фотографии
    if not os.path.exists('photos'):
        os.makedirs('photos')

    # устанавливаем количество страниц для парсинга
    quantity_of_pages = 3

    df = pd.DataFrame(columns=['Название', 'год выпуска', 'Пробег', 'Цена', 'Продавец', 'Рейтинг'])


    for i in range(1, quantity_of_pages+1):
        html_page = get_html_page(f"https://www.avito.ru/sergiev_posad/avtomobili/bmw-ASgBAgICAUTgtg3klyg?p={i}&radius=200&searchRadius=200")
        parse_html(html_page, df)
