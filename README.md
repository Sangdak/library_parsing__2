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

## How to use
In the terminal, go to the repository directory and run the command
```Python
python3 parse_tululu.py 1 10
```
For books with `id` numbers from `1` to `10`, texts will be downloaded 
(nested `books` directory) and book covers (subdirectory `images` ).
All nested directories are created automatically

If there is no option to download the text on the book page, in 
the terminal window  a corresponding warning will appear.

Also, the Terminal will display the titles for downloaded books, 
their genres and comments to them (if any exists).


## Project Goals

The code is written for educational purposes - this is a lesson 
in the course on Python and web development on the [Devman] 
site (https://dvmn.org).