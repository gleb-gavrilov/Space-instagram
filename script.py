from pathlib import Path
import requests
from tqdm import tqdm
from PIL import Image
import instabot
from os import listdir
import argparse


def download_image(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    file_type = get_file_type(url)
    with open(f'images/{filename}.{file_type}', 'wb') as file:
        file.write(response.content)


def get_file_type(file):
    return file.split('.')[-1]


def get_hubble_image_link(id):
    response = requests.get(f'http://hubblesite.org/api/v3/image/{id}')
    response.raise_for_status()
    link_image = ''
    for images in response.json()['image_files']:
        for key, value in images.items():
            if key == 'file_url':
                link_image = value.replace('//', 'https://')
    return link_image


def get_hubble_images_id(collection):
    response = requests.get(f'http://hubblesite.org/api/v3/images/{collection}')
    response.raise_for_status()
    image_ids = []
    [image_ids.append(api_answer['id']) for api_answer in response.json()]
    return image_ids


def get_image_links(year):
    url = 'https://api.spacexdata.com/v3/launches/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
    }
    params = {
        'launch_year': year
    }
    image_links = []
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    for api_answer in response.json():
        [image_links.append(image) for image in api_answer['links']['flickr_images']]
    return image_links


def fetch_spacex_last_launch(year):
    image_links = get_image_links(year)
    for image_id, image_link in tqdm(enumerate(image_links)):
        download_image(image_link, f'space{image_id}')


def fetch_hubble_images(collection):
    image_ids = get_hubble_images_id(collection)
    for image_id in tqdm(image_ids):
        image = get_hubble_image_link(image_id)
        download_image(image, f'{collection}_{image_id}')


def resize_image_for_instagram():
    images = listdir('images')
    for image in tqdm(images):
        new_image = Image.open(f'images/{image}')
        new_width = 1080 if new_image.width > 1080 else new_image.width
        new_height = 1080 if new_image.height > 1080 else new_image.height
        new_image.thumbnail((new_width, new_height))
        new_image.save(f'images_for_inst/{image}', format='JPEG')


def create_default_folders():
    Path('images_for_inst').mkdir(parents=True, exist_ok=True)
    Path('images').mkdir(parents=True, exist_ok=True)


def send_images_to_instagram(login, password):
    files = listdir('images_for_inst')
    images = filter(lambda x: x.endswith('.jpg'), files)
    bot = instabot.Bot()
    bot.login(username=login, password=password)
    for image in tqdm(images):
        bot.upload_photo(f'images_for_inst/{image}')


def init_args():
    parser = argparse.ArgumentParser(description='Скачивание и отправка фотографий в инстаграм.')
    parser.add_argument('-login', type=str, help='Логин от инстаграм аккаунта.')
    parser.add_argument('-password', type=str, help='Пароль от инстаграм аккаунта.')
    parser.add_argument('-get_images', type=bool, default=False, help='Запускает скачиваение фотографий.')
    parser.add_argument('-send_images', type=bool, default=False, help='Отправить фотографии в инстаграм.')
    parser.add_argument('-spacex_year_images', type=int, default=2019, help='Год spaceX фотографий.')
    parser.add_argument('-hubble_collection_images',
                        type=str,
                        choices=['holiday_cards', 'wallpaper', 'spacecraft', 'news', 'printshop', 'stsci_gallery'],
                        default='spacecraft',
                        help='Какую коллекцию от hubble скачивать.')
    return parser.parse_args()


def main():
    args = init_args()
    create_default_folders()
    try:
        if args.get_images:
            fetch_spacex_last_launch(args.spacex_year_images)
            fetch_hubble_images(args.hubble_collection_images)
            resize_image_for_instagram()
        if args.login and args.password and args.send_images:
            send_images_to_instagram(args.login, args.password)
    except requests.exceptions.HTTPError as error:
        print(f'Can`t get data from server:\n{error}')


if __name__ == '__main__':
    main()