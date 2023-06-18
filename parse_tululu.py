import os.path
from time import sleep
from pathlib import Path
from urllib.parse import urlparse, urljoin
from pathvalidate import sanitize_filename
import argparse
import requests
from bs4 import BeautifulSoup
import json


def create_parser():
    parser = argparse.ArgumentParser(
        prog='get_books',
        description='Downloading books by category from "tululu.org".',
    )

    parser.add_argument(
        '-cat',
        '--category_page',
        help='URL to section (genre) of library. For example: '
             '"https://tululu.org/l55/" - "Non-fiction" (as default)',
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
        help='Specify directory for saving the results '
             '(by default books saves in "books/" '
             'and images saves in "images/" in the script folder).',
        type=str,
    )
    parser.add_argument(
        '-j',
        '--json_path',
        help='Specify directory for "results.json" file with results '
             '(by default it saves in the script folder).',
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


def get_book_urls_by_category(
        book_category_id: str,
        start_page_number: int,
        end_page_number: int
) -> list[str]:
    book_urls: list = []
    for page_number in range(start_page_number, end_page_number + 1):
        page_handling_attempts = 5
        while page_handling_attempts:
            try:
                category_page_url: str = \
                    f'https://tululu.org/{book_category_id}/{page_number}/'
                response = requests.get(category_page_url)
                response.raise_for_status()
                check_for_redirect(response)

                bsoup_content = BeautifulSoup(response.text, 'lxml')

                for raw_book_url_string in bsoup_content.select('table.d_book'):
                    book_url = urljoin(
                        response.url,
                        str(raw_book_url_string.select('a')).split('/')[1],
                    )
                    book_urls.append(book_url)

            except requests.ConnectionError:
                print(f'Не удалось извлечь данные со страницы #{page_number}. '
                'Проверьте состояние вашего интернет-соединения.')
                print(f'Выполняется повторная попытка обработки страницы #{page_number}')
                print(f'Количество оставшихся попыток переподключения: '
                f'{page_handling_attempts}/5.')
                sleep(10)
                page_handling_attempts -= 1
            except requests.HTTPError:
                print(f'Не удалось извлечь данные со страницы #{page_number}. '
                'Проверьте есть ли у вас требуемые  права доступа и существует ли страница .')
                print(f'Выполняется повторная попытка обработки страницы #{page_number}')
                print(f'Количество оставшихся попыток переподключения: '
                f'{page_handling_attempts}/5.')
                sleep(10)
                page_handling_attempts -= 1
            else:
                page_handling_attempts = False

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
    book_cover_image_url: str = \
        urljoin(response.url, book_cover_image_tag['src'])

    book_comments: list[str] = \
        [tag.text for tag in soup.select('div.texts span')]

    book_genres: list[str] = [tag.text for tag in soup.select('span.d_book a')]

    return {'title': book_title,
            'author': book_author,
            'cover_url': book_cover_image_url,
            'comments': book_comments,
            'genres': book_genres,
            }


def download_book_txt(
        book_id: int,
        filename: str,
        destination: Path,
        folder: str = 'books/'
) -> str:
    """Скачать текстовый файл книги.

    Args:
        book_id (str): Номер скачиваемой книги на сайте.
        filename (str): Имя сохраняемого файла.
        destination (str): Путь для сохранения.
        folder (str): Папка для сохранения. По умолчанию `books/`.

    Returns:
        str: Путь до сохранённого файла.

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


def download_book_cover(
        url: str,
        destination: Path,
        folder: str = 'images/'
) -> str:
    """Скачать изображения обложек книг.

    Args:
        url (str): Ссылка на изображение обложки, которое необходимо скачать.
        destination (Path): Путь для сохранения.
        folder (str): Папка, куда сохранять. По умолчанию "images/"

    Returns:
        filepath (str): Путь до файла изображения обложки.

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
    parser = create_parser()
    args = parser.parse_args()

    if args.start_page <= args.finish_page:
        print('Начинается обработка.')
    else:
        print(
            'Пожалуйста, ознакомьтесь со справочной информацией '
            'к данному скрипту',
        )
        parser.print_help()

    books_category: str = args.category_page.split('/')[-2]

    book_urls: list[str] = get_book_urls_by_category(
        books_category,
        args.start_page, args.finish_page,
    )
    book_number_ids: list[int] = \
        [int(b.split('/')[-1][1:]) for b in book_urls]

    books_annotations: list = []

    for book_id in book_number_ids:
        number_of_connection_attempts = 5

        while number_of_connection_attempts:

            try:
                book_page_response = get_book_page(book_id)
                book: dict = parse_book_page(book_page_response)

                txt_name: str = f"{book_id}.{book['title']}"

                genres = book['genres'] if book['genres'] \
                    else 'There is no genres for this book!'
                comments = book['comments'] if book['comments'] \
                    else 'There is no comments for this book'

                book_describe = {
                    'title': book['title'],
                    'author': book['author'],
                    'comments': comments,
                    'genres': genres,
                }

                if not args.skip_texts:
                    text_path = download_book_txt(
                        book_id,
                        txt_name,
                        Path(args.destination_path)
                        if args.destination_path else Path.cwd(),
                    )
                    book_describe['book_path'] = text_path

                if not args.skip_images:
                    cover_path = download_book_cover(
                        book['cover_url'],
                        Path(args.destination_path)
                        if args.destination_path else Path.cwd(),
                    )
                    book_describe['img_src'] = cover_path

                if os.path.exists(book_describe['book_path']):
                    books_annotations.append(book_describe)

                break

            except requests.HTTPError:
                print('Can\'t create book. Maybe it doesn\'t exist!')

                break

            except requests.ConnectionError:
                print('There is a problem with the network connection,\n'
                      'and all attempts to reconnect have been exhausted.\n'
                      'Try again later or contact your administrator.')

                print('Number of connection attempts: ',
                      number_of_connection_attempts,
                      )
                print('Waiting 10 seconds before retry.')
                print()
                sleep(10)

                number_of_connection_attempts -= 1

    json_filepath = os.path.join(
        Path(args.json_path) if args.json_path else Path.cwd(),
        'results.json'
    )
    with open(json_filepath, 'a', encoding='utf-8') as file:
        json.dump(books_annotations, file, indent=True, ensure_ascii=False)

    print('Работа программы завершена')
    exit()


if __name__ == '__main__':
    main()
