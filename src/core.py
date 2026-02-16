import os
from abc import ABC, abstractmethod

try:
    from kivy.graphics.texture import Texture
    import fitz
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

class BookFormat(ABC):
    @abstractmethod
    def parse_metadata(self, file_path):
        pass
    
    @abstractmethod
    def open_document(self, file_path):
        pass

    @abstractmethod
    def get_page_texture(self, doc, page_num, scale=2):
        pass

    @abstractmethod
    def get_cover_texture(self, file_path):
        pass

class BaseMuPDFBook(BookFormat):
    def parse_metadata(self, file_path):
        filename = os.path.basename(file_path)
        clean_title = os.path.splitext(filename)[0]
        author = "Неизвестный автор"
        
        if HAS_LIBS:
            try:
                doc = fitz.open(file_path)
                meta = doc.metadata
                if meta.get('title') and meta['title'].strip(): 
                    clean_title = meta['title']
                if meta.get('author') and meta['author'].strip(): 
                    author = meta['author']
                doc.close()
            except:
                pass
        return {"title": clean_title, "author": author}

    def open_document(self, file_path):
        if not HAS_LIBS:
            raise ImportError("Установите PyMuPDF: pip install pymupdf")
        return fitz.open(file_path)

    def get_page_texture(self, doc, page_num, scale=2):
        """
        Рендерит страницу в текстуру Kivy.
        Работает и для PDF, и для EPUB (fitz сам верстает EPUB).
        """
        if not HAS_LIBS: return None
        try:
            page = doc.load_page(page_num)
            mat = fitz.Matrix(scale, scale) 
            pix = page.get_pixmap(matrix=mat)
            texture = Texture.create(size=(pix.width, pix.height), colorfmt='rgb')
            texture.blit_buffer(pix.samples, colorfmt='rgb', bufferfmt='ubyte')
            texture.flip_vertical()
            return texture
        except Exception as e:
            print(f"Error rendering page: {e}")
            return None

    def get_cover_texture(self, file_path):
        if not HAS_LIBS: return None
        try:
            doc = fitz.open(file_path)
            texture = self.get_page_texture(doc, 0, scale=0.8) 
            doc.close()
            return texture
        except Exception:
            return None

class PDFBook(BaseMuPDFBook):
    pass

class EpubBook(BaseMuPDFBook):
    pass

class BookParserFactory:
    @staticmethod
    def get_parser(file_path):
        ext = file_path.lower()
        if ext.endswith('.pdf'):
            return PDFBook()
        elif ext.endswith('.epub'):
            return EpubBook()
        else:
            raise ValueError("Unsupported format")