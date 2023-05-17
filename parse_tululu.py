import os.path
from pathlib import Path
from urllib.parse import urlparse, urljoin
from pathvalidate import sanitize_filename
from time import sleep
import argparse
import json

from bs4 import BeautifulSoup
import requests


def create_parser():
    parser = argparse.ArgumentParser(prog='get_books', description='Downloading books by category from "tululu.org".')

    parser.add_argument(
        '-cat',
        '--category_page',
        help='URL to section (genre) of library. For example: "https://tululu.org/l55/" - "Non-fiction" (as default)',
        type=str,
        default='https://tululu.org/l55/',
    )
    parser.add_argument(
        '-s',
        '--start_page',
        help='Start page for downloading (input a number)',
        type=int,
        default=1,
    )
    parser.add_argument(
        '-f',
        '--finish_page',
        help='Finish page for downloading (input a number)',
        type=int,
        default=1,
    )
    parser.add_argument(
        '-d',
        '--destination_path',
        help='Specify directory for saving the results (by default books saves in "books/" '
             'and images saves in "images/" in the script folder).',
        type=str,
    )
    parser.add_argument(
        '-j',
        '--json_path',
        help='Specify directory for "results.json" file with results (by default it saves in the script folder).',
        type=str,
    )
    parser.add_argument(
        '-i',
        '--skip_images',
        help='Specify to not download pictures (default is "False").',
        action='store_true',
    )
    parser.add_argument(
        '-t',
        '--skip_texts',
        help='Specify to not download texts (default is "False").',
        action='store_true',
    )
    return parser


def get_books_by_category(book_category_id: str, start_page_number: int, end_page_number: int) -> list[str]:
    book_urls: list = []
    for page_number in range(start_page_number, end_page_number + 1):
        category_page_url: str = f'https://tululu.org/{book_category_id}/{page_number}/'

        response = requests.get(category_page_url)
        response.raise_for_status()
        if response.history:
            print(f'Обработка завершена, подготовлено к скачиванию {page_number - start_page_number} страниц')

        soup = BeautifulSoup(response.text, 'lxml')

        for soup_item in soup.select('table.d_book'):
            book_url = urljoin('https://tululu.org/', str(soup_item.select('a')).split('/')[1])
            book_urls.append(book_url)

    return book_urls


def get_book_page(book_id: int):
    site = 'https://tululu.org/'
    url = urljoin(site, f'b{book_id}/')

    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    return response


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(response) -> dict:
    soup = BeautifulSoup(response.text, 'lxml')

    book_title_author_tag = soup.find('h1')
    book_title, book_author = book_title_author_tag.text.split('::   ')
    book_title: str = book_title.strip()
    book_author: str = book_author.strip()

    book_cover_image_tag = soup.select_one('div.bookimage img')
    book_cover_image_url: str = urljoin(response.url, book_cover_image_tag['src'])

    book_comments: list[str] = [tag.text for tag in soup.select('div.texts span')]

    book_genres: list[str] = [tag.text for tag in soup.select('span.d_book a')]

    return {'title': book_title,
            'author': book_author,
            'cover_url': book_cover_image_url,
            'comments': book_comments,
            'genres': book_genres,
            }


def download_book_txt(book_id: int, filename: str, destination, folder: str = 'books/') -> str:
    """Функция для скачивания текстовых файлов.
        Args:
            book_id (str): Номер книги, которую хочется скачать.
            filename (str): Имя файла, с которым сохранять.
            destination (str): Папка для сохранения.
            folder (str): Папка, куда сохранять. По умолчанию "books/"
        Returns:
            str: Путь до файла, куда сохранён текст.
        """
    url = 'https://tululu.org/txt.php'
    payload = {'id': book_id}

    path = destination / folder
    path.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)

    filepath = Path(path, sanitize_filename(f'{filename}.txt'))

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return str(filepath)


def download_book_cover(url: str, destination, folder: str = 'images/') -> str:
    """Функция для скачивания изображений обложек книг.
        Args:
            url (str): Cсылка на изображение обложки, которое хочется скачать.
            destination (str): Папка для сохранения.
            folder (str): Папка, куда сохранять. По умолчанию "images/"
        # Returns (str): Путь до файла, куда сохранёна обложка.
        """

    path = destination / folder
    path.mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    filename = urlparse(url).path.split('/')[-1]
    filepath = Path(path, sanitize_filename(filename))

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return str(filepath)


def main():
    connection_waiting_seconds: int = 10

    parser = create_parser()
    args = parser.parse_args()

    category: str = args.category_page
    start: int = args.start_page
    end: int = args.finish_page
    destination_folder = Path(args.destination_path) if args.destination_path else Path.cwd()
    json_path = Path(args.json_path) if args.json_path else Path.cwd()
    skip_img = args.skip_images
    skip_txt = args.skip_texts

    if os.path.isdir(destination_folder) and start <= end:
        print('Начинается обработка.')
    else:
        parser.print_help()

    books_category: str = category.split('/')[-2]

    book_urls: list[str] = get_books_by_category(books_category, start, end)
    book_id_only_numbers: list[int] = [int(b.split('/')[-1][1:]) for b in book_urls]

    books_annotations: list = []

    for book_id in book_id_only_numbers:
        is_connected = True
        connection_tries_number = 5

        while connection_tries_number:
            try:
                book_page_response = get_book_page(book_id)
                book: dict = parse_book_page(book_page_response)

                txt_name: str = f"{book_id}.{book['title']}"

                if not skip_txt:
                    text_path = download_book_txt(book_id, txt_name, destination_folder)

                if not skip_img:
                    cover_path = download_book_cover(book['cover_url'], destination_folder)
                print()
                print(genres := book['genres'] if book['genres'] else 'There is no genres for this book!')
                print(comments := book['comments'] if book['comments'] else 'There is no comments for this book')
                print()

                book_describe = {
                    'title': book['title'],
                    'author': book['author'],
                    'img_src': cover_path,
                    'book_path': text_path,
                    'comments': comments,
                    'genres': genres,
                }

                if os.path.exists(text_path):
                    books_annotations.append(book_describe)

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
            except ValueError as error:
                print(f'Unexpected error: {error}')
                print(f'Book "{txt_name}" loading problem, check the data.')
            connection_tries_number -= 1

    json_filepath = os.path.join(json_path, 'results.json')
    with open(json_filepath, 'a', encoding='utf-8') as file:
        json.dump(books_annotations, file, indent=True, ensure_ascii=False)


if __name__ == '__main__':
    main()
