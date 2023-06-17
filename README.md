# Script for downloading files from the resource https://tululu.org/

This script allows you to download files and get the associated
with them information about the book from the library by its id number:
- Title of the book
- Genres
- Comments (if any)

Additionally, when running the script in the appropriate folders
('books' and 'images') download text files of books and their covers
(if they exist).

## How to install

1. Copy the code from the repository, you can use the CLI:
```command line
git clone <repo url>
```

2. Python3 must be installed on your device.

3. Use pip (or pip3, in case of conflict with Python2) to
install all required dependencies:

```Python
pip install -r requirements.txt
```

```Python
python parse_tululu.py
```
Running the script without additional parameters will activate the download of all books of a certain category according to the list (by default, "Science Fiction") to the current directory.
Book texts are stored in the `books` subdirectory, book covers in the `images` subdirectory.

If it is not possible to download the text of the book, then a warning is displayed in the console.

### Command line options
When running the script, it is recommended to use the following parameters:
* `--category_page` (str). A link to the selected category is provided (for example, 'https://tululu.org/l55/')

```python
python parse_tululu.py --category_page https://tululu.org/l55/
```

* `--start_page`, `-s` (int). Number of the start page of the category section to download. The default is 1.
* `--finish_page`, `-f` (int). The end page of the genre section to download. If not specified, it will download
all pages of the genre to the end.

```python
python parse_tululu.py --start_page 700
python parse_tululu.py --start_page 700 --finish_page 701
```

* `--destination_path`, `-d` (str). Download directory (by default, the root folder of the script).
* `--json_path`, `-j` (str). The name of the file to upload the result. Default: `books_info.json`.
* `--skip_images`, `-i` Specify a "flag" to not upload book covers.
* `--skip_texts`, `-t` Specify a "flag" to not download book texts.


## Project Goals

The code is written for educational purposes - this is a lesson 
in the course on Python and web development on the [Devman](https://dvmn.org) 
site.