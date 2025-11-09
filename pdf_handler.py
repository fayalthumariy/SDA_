from tika import parser

class HandlePDF:
    def __init__(self, pdf_path ):
        '''

        :param pdf_path:
        '''
        self.pdf_path = pdf_path

    def extract_text(self):
        text = parser.from_file(self.pdf_path)
        return text['content']




