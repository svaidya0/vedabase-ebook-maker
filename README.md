# vedabase-ebook-maker

A command line python script that takes the url of a book from vedabase.io and outputs a local epub (ebook) file.

## Installation

_Note this requires Python 3 to run._

Download the veda.py python script and install the following dependencies:

** requests:**
```
pip install requests
```

** BeautifulSoup 4:**
```
pip install beautifulsoup4
```

** PyPandoc:**
```
pip install pypandoc
```

## Usage

Run the script in command line using:

```
python veda.py
```
Then follow the commands to enter the url of the book.

![Terminal Screenshot] (terminal_screenshot.png)

The script will then create a temporary file _VedabaseEbookTempFile.txt_ which will store the text of ebook until the end of the script where it will be converted into an epub file using the Pandoc wrapper - pypandoc.

## Features to be implemented

* Support for all books _(Currently most books on the website are supported but not all)_
* Methods to catch wrong user input
* GUI interface for input
* Added options for user such as a variety of output file formats
* Increased efficiency