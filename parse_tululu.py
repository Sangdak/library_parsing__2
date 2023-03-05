# import os
from time import sleep
import sys
import requests
from pathlib import Path
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import argparse


def get_book_page(book_id):
    site = 'https://tululu.org/'
    url = urljoin(site, f'b{book_id}/')

    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return response


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def create_parser():
    parser = argparse.ArgumentParser(description='Скрипт для последовательного скачивания книг с сайта tululu.org ')
    parser.add_argument('start_index', help='С какого индекса книги (число) нужно начать скачивание', type=int)
    parser.add_argument('end_index', help='Каким индексом книги (число) нужно завершить скачивание', type=int)
    return parser


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')

    book_title_tag = soup.find('h1')
    book_title, author = book_title_tag.text.split('::')
    book_title = book_title.strip()

    cover_image_tag = soup.find('div', class_='bookimage').find('img')
    cover_image_url = urljoin(response.url, cover_image_tag['src'])

    book_comments_tag = soup.find_all('div', class_='texts')
    book_comments = '\n'.join([tag.find('span').text for tag in book_comments_tag])

    book_genre_tag = soup.find('span', class_='d_book').find_all('a')
    book_genres = [tag.text for tag in book_genre_tag]

    return book_title, cover_image_url, book_comments, book_genres


def download_book_txt(book_id, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
        Args:
            # url (str): Cсылка на текст, который хочется скачать.
            book_id (int): Номер книги, которую хочется скачать.
            filename (str): Имя файла, с которым сохранять.
            folder (str): Папка, куда сохранять. По умолчанию "books/"
        Returns:
            str: Путь до файла, куда сохранён текст.
        """
    url = 'https://tululu.org/txt.php'
    payload = {'id': book_id}
    Path(f'./{folder}').mkdir(parents=True, exist_ok=True)

    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)

    filepath = Path(f'./{folder}/{sanitize_filename(filename)}.txt')

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def download_book_cover(url, filename, folder='images/'):
    """Функция для скачивания изображений обложек книг.
        Args:
            url (str): Cсылка на изображение обложки, которое хочется скачать.
            filename (str): Имя файла, с которым сохранять.
            folder (str): Папка, куда сохранять. По умолчанию "images/"
        # Returns:
        #     str: Путь до файла, куда сохранёна обложка.
        """
    Path(f'./{folder}').mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    filepath = Path(f'./{folder}/{sanitize_filename(filename)}')

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


def main():
    connection_waiting_seconds = 10

    parser = create_parser()
    if len(sys.argv) < 3:
        parser.print_help()
    args = parser.parse_args()

    for book_id in range(args.start_index, args.end_index + 1):
        is_connected = True
        number_of_tries = 5

        while number_of_tries > 0:
            try:
                response = get_book_page(book_id)
                book_title, cover_image_url, book_comments, book_genres = parse_book_page(response)

                print(f'!!! !!! !!!{book_title} {cover_image_url} {book_comments} {book_genres}')

                txt_name = f'{book_id}. {book_title}'

                print(download_book_txt(book_id, txt_name))
                print(download_book_cover(cover_image_url, str(book_id)))
                print()
                print(book_genres) if book_genres else print('There is no genres for this book!')
                print(book_comments) if book_comments else print('There is no comments for this book')
                print()
                break
            except requests.ConnectionError:
                if is_connected:
                    is_connected = False
                    print(f'Unsuccessful connection attempt. Pending connection retry.')
                else:
                    print('Missing connection')
                    print(f'Retrying connection via {connection_waiting_seconds} seconds.')
                    sleep(connection_waiting_seconds)
            except requests.HTTPError:
                print(f"Can't create book {txt_name}, it doesn't exist!")
                break
            except Exception as error:
                print(f'Unexpected error: {error}')
                print(f'Book "{txt_name}" loading problem, check the data.')
            number_of_tries -= 1


if __name__ == '__main__':
    main()
