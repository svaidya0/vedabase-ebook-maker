import requests
import io
import os
import pypandoc
from bs4 import BeautifulSoup

# Creates a temporary file to store the text for the ebook
f = open('VedabaseEbookTempFile.txt', 'a', encoding="utf-8")

class Book:
    def __init__(self, link):
        # Url of the book
        self.link = link

        # The html for the contents page of the book
        src = requests.get(self.link)
        self.soup = BeautifulSoup(src.text, 'html.parser' )

        # Gets the title and author of the book
        titleDiv = (self.soup).find('div', class_="mb-3 bb r r-title r-book")
        title = '% ' + str( titleDiv.get_text() ).strip()
        author = '% His Divine Grace A. C. Bhaktivedanta Swami Prabhupāda'
        f.write(title + '\n' + author + '\n')

        # Checks whether the book has cantos
        self.cantosExist = True
        if not (self.soup).find('div', class_="bb r r-canto"):
            self.cantosExist = False
        
        # Checks whether it's a book that directly has verses rather than chapters
        self.directVerses = False
        if (self.soup).find('div', class_="r r-verse"):
            self.directVerses = True
        elif (self.soup).find('div', class_="r bb r-lang-en r-chapter"):
            base_url = "https://vedabase.io"
            for chapter in (self.soup).find_all('div', class_="r bb r-lang-en r-chapter"):
                link = chapter.find('a')
                html = requests.get(base_url + link['href'])
                link_soup = BeautifulSoup(html.text, 'html.parser' )
                if link_soup.find('div', class_="r r-lang-en r-translation"):
                    self.directVerses = True
    
    # Method to the get the  correspondong html soup of a link supplied to it
    def getSoup(self, link):
        base_url = "https://vedabase.io"
        html = requests.get(base_url + link['href'])
        link_soup = BeautifulSoup(html.text, 'html.parser' )
        return link_soup
    
    # Method that saves any verse based text to the temp txt file
    def getVerses(self, chapter):
        
        # Gets the html for the verses, this can't currently be done via the getSoup method
        base_url = "https://vedabase.io"
        url = base_url + str(chapter['href']) + "advanced-view/"
        html = requests.get(url)
        chapter_soup = BeautifulSoup(html.text, 'html.parser' )

        # A string needed for verses
        purport = "**Purport **"

        for t in chapter_soup.find_all('div', class_=["bb r-verse", "r r-devanagari", "r r-lang-en r-verse-text", "r r-lang-en r-synonyms", "r r-lang-en r-translation", "r r-lang-en r-paragraph"]):

            # Verse title - e.g. 'Text 1' - formatted in a way that it's added to contents in the ebook
            if 'bb' in t['class']:
                s = '## ' + t.get_text().strip() + '\n'
                f.write('\n' + s)
                # Sets p to 0 so the purport string can be used below the verse 
                p = 0
                continue
            
            # Adjusts markdown formatting for the actual verses
            elif 'r-verse-text' in t['class']:
                output = pypandoc.convert_text(str(t), 'markdown', format='html')
                output = output.replace("**", "*")
                output = output.replace("*\\", "\\")
                f.write(output)
                continue
            
            # Writes the commentary given on the verses
            elif "r-paragraph" in t['class']:
                if p == 0:
                    f.write('\n' + purport + '\n' + '\n')
                    p = 1
            
            output = pypandoc.convert_text(str(t), 'markdown', format='html')
            f.write(output)

    # Method that saves text from a chapter of the book
    def writeChapter(self, chapter_soup, chapter_link):
        
        # Checks whether the chapter contains verses and calls getVerses
        if chapter_soup.find('dl', class_="r r-verse"):
            self.getVerses(chapter_link)
            return
        
        for t in chapter_soup.find_all('div', class_=["r r-lang-en r-verse-text", "r r-lang-en r-paragraph", "r r-lang-en r-paragraph-intro", "r r-lang-en r-sub-chapter", "r r-lang-en r-paragraph-list"]):
            if 'r-paragraph-intro' in t['class']:
                # Adjusts the markdown formatting for italicized intro paragraphs before writing
                output = '*' + pypandoc.convert_text(str(t), 'markdown', format='html') + '*'
                f.write(output)
                continue
            elif 'r-sub-chapter' in t['class']:
                # Adjusts the markdown formatting for subtitles within the chapter before writing
                output = '## ' + t.get_text().strip() + '\n'
                f.write('\n' + output)
                continue

            output = pypandoc.convert_text(str(t), 'markdown', format='html')
            f.write(output)

    # Iterates through all the cantos and chapters within the book
    def buildBook(self):

        #If the book has cantos:
        if self.cantosExist:

            for canto in (self.soup).find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter", "bb r r-canto"]):
                canto_soup = self.getSoup(canto.find('a'))
                
                # If statement to account for some books having chapters outside cantos 
                if 'r-canto' in canto['class']:
                    
                    # Gets and formats the title of the canto
                    title = '# ' + str((canto.find('a')).get_text()).strip()
                    
                    f.write(title + '\n' + '\n')

                    for chapter in canto_soup.find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"] ):
                        chapter_link = chapter.find('a')
                        chapter_soup = self.getSoup(chapter_link)
                        
                        # Gets and formats the title of the chapter
                        title = '## ' + str((chapter.find('a')).get_text()).strip()
                        
                        f.write(title + '\n' + '\n')
                        self.writeChapter(chapter_soup, chapter_link)
                
                else:
                    chapter_link = canto.find('a')
                    
                    # Gets and formats the title of the chapter
                    title = '# ' + str((canto.find('a')).get_text()).strip()
                    
                    f.write(title + '\n' + '\n')
                    self.writeChapter(canto_soup, chapter_link)
        
        # If the book doesn't have cantos
        else:
            for chapter in (self.soup).find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"]):
                chapter_link = chapter.find('a')
                chapter_soup = self.getSoup(chapter_link)
                
                # Gets and formats the title of the chapter
                title = '# ' + str((chapter.find('a')).get_text()).strip()
                
                f.write(title + '\n' + '\n')
                self.writeChapter(chapter_soup, chapter_link)


# User input for url of the book
book_url = str(input("Enter url:" ))

book = Book(book_url)
book.buildBook()
f.close()

# Creates name of the ebook file
f = open('VedabaseEbookTempFile.txt', 'r', encoding="utf-8")
ebookName = str(f.readline().split('%')[1]).strip() + '.epub'
ebookName = ebookName.replace(":", "")
ebookName = ebookName.replace("?", "")
print(ebookName)
f.close()

# Converts VedabaseEbookTempFile.txt to an ebook
pypandoc.convert_file('VedabaseEbookTempFile.txt', 'epub', format ="markdown", outputfile = ebookName)

# Deletes VedabaseEbookTempFile.txt
if os.path.exists("VedabaseEbookTempFile.txt"):
    os.remove("VedabaseEbookTempFile.txt")