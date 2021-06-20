import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile
import os

def create_contents(chapters_soup, incanto = 0):
    chapter_link = chapters_soup.find('a')
    contents.append(base_url + chapter_link['href'])
    chapter_title = chapter_link.get_text()
    if chapter_title[-1] == ':':
        chapter_title = chapter_title[:-1]
    chapter_titles.append(chapter_title.strip())
    chapter_id = chapter_title.replace(': ', '-')
    chapter_id = chapter_id.replace(' ', '-')
    chapter_ids.append(chapter_id.strip())
    f = open('epub_contents.xhtml', 'a', encoding="utf-8")
    f.write('<li><a href="epub_main.xhtml#' + chapter_ids[-1] + '">' + chapter_titles[-1] + '</a>')
    if not incanto:
        f.write('</li>\n')
    f.close()

def end_contents():
    f = open('epub_contents.xhtml', 'a', encoding="utf-8")
    f.write('</ol>\n</nav>\n</body>\n</html>')
    f.close()

url = str(input("Enter url:" ))
base_url = "https://vedabase.io"
src = requests.get(url)
soup = BeautifulSoup(src.text, 'html.parser')

# Creates title page for book
f = open('epub_title.xhtml', 'a', encoding="utf-8")
title = soup.find('div', class_="mb-3 bb r r-title r-book").get_text().strip()
title_html1 = '<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8"/><title>'
title_html2 = '</title></head>\n<body>\n<h1 class="titlepage">'
title_html3 = '</h1>\n</body></html>'
f.write(title_html1 + title + title_html2 + title + title_html3)
f.close()

# Creates contents file
f = open('epub_contents.xhtml', 'a', encoding="utf-8")
contents_html1 = '<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n<head>\n<meta charset="utf-8" />\n<title>Contents</title>\n</head>\n<body>\n<nav epub:type="toc" id="toc">\n<h1 class="title">Contents</h1>\n<ol>\n'
f.write(contents_html1)
contents = list()
chapter_ids = list()
chapter_titles = list()
f.close()

# If the book directly has verses:
if soup.find('dl', class_="r r-verse"):
    for chapters in soup.find_all('div', class_=["bb r r-lang-en r-chapter", "r-verse"]):
        create_contents(chapters)
    end_contents()

# If the book has cantos:
elif soup.find('div', class_=["bb r r-canto", "col-6 col-sm-4 col-md-3 col-lg-2 col-lg-15 text-center book-item"]):
    for canto in soup.find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter", "bb r r-canto", "col-6 col-sm-4 col-md-3 col-lg-2 col-lg-15 text-center book-item"]):
        canto_src = requests.get(base_url + (canto.find('a')['href']))
        canto_soup = BeautifulSoup(canto_src.text, 'html.parser')
        
        # If-else block to account for some books having chapters outside cantos 
        if ('r-canto' in canto['class']) or ('book-item' in canto['class']):
            create_contents(canto, 1)
            f = open('epub_contents.xhtml', 'a', encoding="utf-8")
            f.write('<ol hidden="">\n')
            f.close()

            for chapter in canto_soup.find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"] ):
                create_contents(chapter)
            f = open('epub_contents.xhtml', 'a', encoding="utf-8")
            f.write('</ol>\n</li>\n')
            f.close()
        else:
            create_contents(canto)
    end_contents()

# If the book doesn't have cantos
else:
    for chapter in soup.find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"]):
        create_contents(chapter)
    end_contents()

f = open('epub_main.xhtml', 'a', encoding="utf-8")
f.write('<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8"/><title>' + title + '</title></head><body>\n')

# Gets and writes main text of ebook
for i in range(len(contents)):
    f.write('<div id="' + chapter_ids[i] + '">')
    chapter_src = requests.get(contents[i])
    chapter_soup = BeautifulSoup(chapter_src.text, 'html.parser')

    if chapter_soup.find('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"] ):
        f.write('<h1>' + chapter_titles[i] + '</h1></div>\n')
        continue

    # If chapter is made of verses
    if chapter_soup.find('dl', class_="r r-verse"):
        chapter_src = requests.get(contents[i] + "advanced-view/")
        chapter_soup = BeautifulSoup(chapter_src.text, 'html.parser')

    divs = chapter_soup.find('div', id='content')
    
    # Removes hyperlinks
    for urls in divs.find_all('a'):
        urls.unwrap()
    
    f.write(str(divs).strip())
    f.write('</div>')
f.write('</body></html>')
f.close()

# Some metadata files
f = open('package.opf', 'a', encoding="utf-8")
f.write('<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0">\n<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n<dc:title>' + title + '</dc:title>\n<dc:language>en</dc:language>\n</metadata>')
f.write('<manifest>\n<item href="epub_title.xhtml" id="ttl" media-type="application/xhtml+xml"/>\n<item href="epub_contents.xhtml" id="nav" media-type="application/xhtml+xml" properties="nav"/>\n<item href="epub_main.xhtml" id="main" media-type="application/xhtml+xml"/>\n</manifest>')
f.write('<spine>\n<itemref idref="ttl"/>\n<itemref idref="nav" linear="no"/>\n<itemref idref="main"/>\n</spine>\n</package>')
f.close()
f = open('mimetype', 'a')
f.write('application/epub+zip')
f.close()

# Createst the ebook file
filename = str(title.replace(':', '') + '.epub')
zipObj = ZipFile(filename, 'w')
zipObj.write('epub_title.xhtml')
zipObj.write('epub_contents.xhtml')
zipObj.write('epub_main.xhtml')
zipObj.write('package.opf')
zipObj.write('mimetype')
zipObj.close()
os.remove('epub_title.xhtml')
os.remove('epub_contents.xhtml')
os.remove('epub_main.xhtml')
os.remove('package.opf')
os.remove('mimetype')
print('\nDone!')