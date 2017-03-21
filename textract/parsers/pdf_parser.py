import os
from tempfile import mkdtemp, mkstemp

from ..exceptions import UnknownMethod, ShellError

from .utils import ShellParser
from .image import Parser as TesseractParser


class Parser(ShellParser):
    """Extract text from pdf files using either the ``pdftotext`` method
    (default) or the ``pdfminer`` method.
    """

    def extract(self, filename, method='', **kwargs):
        if method == '' or method == 'pdftotext':
            try:
                return self.extract_pdftotext(filename)
            except ShellError as ex:
                # If pdftotext isn't installed and the pdftotext method
                # wasn't specified, then gracefully fallback to using
                # pdfminer instead.
                if method == '' and ex.is_uninstalled():
                    return self.extract_pdfminer(filename)
                else:
                    raise ex

        elif method == 'pdfminer':
            return self.extract_pdfminer(filename)
        elif method == 'tesseract':
            return self.extract_tesseract(filename)
        else:
            raise UnknownMethod(method)

    def extract_pdftotext(self, filename):
        """Extract text from pdfs using the pdftotext command line utility."""
        stdout, _ = self.run('pdftotext "%(filename)s" -' % locals())
        return stdout

    def convert_pdf_to_txt(self, path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = file(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                      check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()
        return text

    def extract_pdfminer(self, filename):
        """Extract text from pdfs using pdfminer."""
        # stdout, _ = self.run('pdf2txt.py "%(filename)s"' % locals())
        stdout = self.convert_pdf_to_txt(filename)
        return stdout

    def extract_tesseract(self, filename):
        """Extract text from pdfs using tesseract (per-page OCR)."""
        temp_dir = mkdtemp()
        base = os.path.join(temp_dir, 'conv')
        stdout, _ = self.run('pdftoppm "%s" "%s"' % (filename, base))

        contents = []
        for page in os.listdir(temp_dir):
            page_path = os.path.join(temp_dir, page)
            page_content = TesseractParser().extract(page_path)
            contents.append(page_content)
        return '\n\n'.join(contents)
