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
        
    # Method to the get the  correspondong html soup of a link supplied to it
    def getSoup(self, link, forVerse = 0):
        base_url = "https://vedabase.io"

        if forVerse:
            # Special case for chapters containing verses
            html = requests.get(base_url + str(link['href']) + "advanced-view/")
        else:
            html = requests.get(base_url + link['href'])
        link_soup = BeautifulSoup(html.text, 'html.parser' )
        return link_soup
    
    def writeVerse(self, chapter_soup, inCanto):
        
        # For formatting needed for verses
        purport = "**Purport **"
        p=1

        for t in chapter_soup.find_all('div', class_=["bb r-verse", "r r-devanagari", "r r-lang-en r-verse-text", "r r-lang-en r-synonyms", "r r-lang-en r-translation", "r r-lang-en r-paragraph", "r r-bengali"]):

            # Verse title - e.g. 'Text 1' - formatted in a way that it's added to contents in the ebook
            if 'bb' in t['class']:
                s = '## ' + t.get_text().strip() + '\n'
                if inCanto:
                    s = '#' + s
                f.write('\n' + s)
                continue
            
            # Adjusts markdown formatting for the actual verses
            elif 'r-verse-text' in t['class']:
                output = pypandoc.convert_text(str(t), 'markdown', format='html')
                output = output.replace("**", "*")
                output = output.replace("*\\", "\\")
                f.write(output)
                continue
            
            elif 'r-translation' in t['class']:
                # Sets p to 0 so the purport string can be used below the verse 
                p = 0

            # Writes the commentary given on the verses
            elif "r-paragraph" in t['class']:
                if p == 0:
                    f.write('\n' + purport + '\n' + '\n')
                    p = 1
            
            output = pypandoc.convert_text(str(t), 'markdown', format='html')
            # Fixes formatting issue
            output = output.replace('*"', '"*')
            f.write(output)

    # Method that saves text from a chapter of the book
    def writeChapter(self, chapter_soup, chapter_link, inCanto):
        
        chapter_soup = BeautifulSoup(str(chapter_soup).replace("<strong><strong>", "<strong>"), 'html.parser')
        chapter_soup = BeautifulSoup(str(chapter_soup).replace("</strong></strong>", "</strong>"), 'html.parser')

        # Checks whether the chapter contains verses and calls writeVerse
        if chapter_soup.find('dl', class_="r r-verse"):
            chapter_soup = self.getSoup(chapter_link, 1)
            self.writeVerse(chapter_soup, inCanto)
            return
        # Checks whether the chapter is a verse and calls writeVerse
        elif chapter_soup.find('div', class_="r r-lang-en r-synonyms"):
            self.writeVerse(chapter_soup, inCanto)
            return
        
        for t in chapter_soup.find_all('div', class_=["r r-lang-en r-verse-text", "r r-lang-en r-paragraph", "r r-lang-en r-paragraph-intro", "r r-lang-en r-sub-chapter", "r r-lang-en r-paragraph-list", "r r-lang-en r-translation"]):
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
            elif 'r-verse-text' in t['class']:
                output = pypandoc.convert_text(str(t), 'markdown', format='html')
                output = output.replace("**", "*")
                output = output.replace("*\\", "\\")
                f.write(output)
                continue
            
            output = pypandoc.convert_text(str(t), 'markdown', format='html')
            # Fixes formatting issue
            output = output.replace('*"', '"*')
            f.write(output)

    def getChapter(self, chapter, inCanto = 0):
        chapter_link = chapter.find('a')
        chapter_soup = self.getSoup(chapter_link)
        
        # Gets and formats the title of the chapter
        if inCanto:
            title = '## ' + str(chapter_link.get_text()).strip()
            print('     Now getting: ' + str(chapter_link.get_text()).strip())
        else:
            title = '# ' + str(chapter_link.get_text()).strip()
            print('Now getting: ' + str(chapter_link.get_text()).strip())
        
        f.write(title + '\n' + '\n')
        self.writeChapter(chapter_soup, chapter_link, inCanto)

    # Iterates through all the cantos and chapters within the book
    def buildBook(self):

        #If the book directly has verses:
        if (self.soup).find('dl', class_="r r-verse"):
            for chapter in (self.soup).find_all('div', class_=["bb r r-lang-en r-chapter", "r-verse"]):
                self.getChapter(chapter)

        #If the book has cantos:
        elif (self.soup).find('div', class_=["bb r r-canto", "col-6 col-sm-4 col-md-3 col-lg-2 col-lg-15 text-center book-item"]):

            for canto in (self.soup).find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter", "bb r r-canto", "col-6 col-sm-4 col-md-3 col-lg-2 col-lg-15 text-center book-item"]):
                canto_soup = self.getSoup(canto.find('a'))
                
                # If-else block to account for some books having chapters outside cantos 
                if ('r-canto' in canto['class']) or ('book-item' in canto['class']):
                    
                    # Gets and formats the title of the canto
                    title = '# ' + str((canto.find('a')).get_text()).strip()
                    print('Inside ' + str((canto.find('a')).get_text()).strip() + ':')
                    
                    f.write(title + '\n' + '\n')

                    for chapter in canto_soup.find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"] ):
                        self.getChapter(chapter, 1)
                
                else:
                    self.getChapter(canto)
        
        # If the book doesn't have cantos
        else:
            for chapter in (self.soup).find_all('div', class_=["bb r r-lang-en r-chapter", "r bb r-lang-en r-chapter"]):
                self.getChapter(chapter)


###### Main Function (cannot implement as 'def main:' due to opened file)

print("\nVedabase-ebook-maker v0.3.0\n \nPlease enter a valid url from vedabase.io below.")

# User input for url of the book

book_url = str(input("Enter url:" ))
print("\n")

try:
    book = Book(book_url)
    book.buildBook()
    f.close()

    # Creates name of the ebook file
    f = open('VedabaseEbookTempFile.txt', 'r', encoding="utf-8")
    ebookName = str(f.readline().split('%')[1]).strip() + '.epub'
    ebookName = ebookName.replace(":", "")
    ebookName = ebookName.replace("?", "")
    f.close()

    # Converts VedabaseEbookTempFile.txt to an ebook
    pypandoc.convert_file('VedabaseEbookTempFile.txt', 'epub', format ="markdown", outputfile = ebookName)
    print("\nDone!")

    # Deletes VedabaseEbookTempFile.txt
    if os.path.exists("VedabaseEbookTempFile.txt"):
        os.remove("VedabaseEbookTempFile.txt")
except:
    f.close()
    if os.path.exists("VedabaseEbookTempFile.txt"):
        os.remove("VedabaseEbookTempFile.txt")
    print("\nSorry there was an error! Please report to svaidya0 on GitHub, thank you :)")