from pypdf import PdfWriter
from pypdf.generic import NameObject, DictionaryObject, NumberObject, TextStringObject


class PdfExtender:
    EXTENSION_PREFIX = "/DANV"
    EXTENSION_NAME = '/DANV_SlideVideoSync'
    INTERVALS_SUBKEY_NAME = r"/SlideAppearanceIntervals"
    EXTENSION_VERSION = 1
    EXTENSION_URL = r"https://github.com/DanValnicek/pdf-ext-slide-video-sync"

    @staticmethod
    def add_extension_info(pdf_writer: PdfWriter):
        pdf_writer.root_object.update(DictionaryObject({
            NameObject("/Type"): NameObject("/Catalog"),
            NameObject("/Extensions"): DictionaryObject({
                NameObject("/Type"): NameObject("/DeveloperExtensions"),
                NameObject(PdfExtender.EXTENSION_PREFIX): DictionaryObject({
                    NameObject("/BaseVersion"): NameObject("/2.0"),
                    NameObject("/ExtensionLevel"): NumberObject(PdfExtender.EXTENSION_VERSION),
                    NameObject("/URL"): TextStringObject(PdfExtender.EXTENSION_URL)
                })
            })
        }))
