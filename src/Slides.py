import logging
from abc import ABC
from math import sqrt
from pathlib import Path
from typing import List, Tuple

from PIL.Image import Image
from pymupdf import pymupdf


class SlidesCreator:
    _registry = {}

    @classmethod
    def register(cls, extension: str):
        """Registers a class for processing presentations with a given extension.
        So that the Presentation class can instantiate it."""

        def inner_wrapper(wrapped_class):
            cls._registry[extension] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @classmethod
    def get(cls, extension: str):
        if extension not in cls._registry:
            raise ValueError(f'Unknown extension {extension}')
        return cls._registry[extension]


# Base decorator class for Image
class ImageDecorator(ABC):
    def __init__(self, img: Image) -> None:
        self._img_decor = img

    @property
    def image(self) -> Image:
        return self._img_decor

    def __getattr__(self, method_name):
        """Delegate method calls to the wrapped image."""
        return getattr(self._img_decor, method_name)


# A decorator for Presentation slides that uses ImageDecorator to wrap images
class Slide(ImageDecorator):
    def __init__(self, img: Image, page_number: int, presentation: "Slides") -> None:
        super().__init__(img)
        self.presentation = presentation
        self.page_number = page_number

    # Example additional method added by the decorator
    def get_page_number(self):
        return self.page_number

    def get_size(self) -> Tuple[int, int]:
        """@returns width, height of the image"""
        return self.image.size


# Abstract base class for Presentation, with factory method to load correct class based on file extension
class Slides(ABC):

    def get_slide(self, slide_number: int) -> Slide:
        ...

    def get_all_slides(self):
        ...

    def set_slide(self, slide_number: int, value: ImageDecorator):
        ...

    def get_slide_cnt(self):
        ...

    def __new__(cls, path: Path):
        # Dynamically assign class based on file extension
        if cls is Slides:
            cls = SlidesCreator.get(path.suffix)
        return super().__new__(cls)

    def get_pdf_file_path(self):
        """
            Get a path to pdf representation of slides.
            If the type is not native PDF a conversion to PDF has to be made and saved temporarily.
        """
        raise NotImplementedError()

    def __init__(self, path: Path):
        pass


# Register PdfPresentation for .pdf extension
@SlidesCreator.register('.pdf')
class PdfSlides(Slides):
    _slides: List[Slide]

    def __init__(self, path: Path):
        self.path = Path(path)
        # Convert PDF to list of images (one per page)
        slides = []
        for page in pymupdf.open(self.path):
            pdf_width, pdf_height = page.rect.width / 72, page.rect.height / 72
            corrected_width = 480 / pdf_height * pdf_width
            dpi = max(round(sqrt(480 * corrected_width / (pdf_width * pdf_height))), 1)
            slides.append(page.get_pixmap(dpi=dpi).pil_image())
        self._slides = [Slide(img=img, page_number=i, presentation=self) for i, img in
                        enumerate(slides)]

        logging.getLogger(__name__).debug("file count: " + str(self.get_slide_cnt()))

    def get_pdf_file_path(self):
        return self.path

    def get_slide(self, slide_number: int) -> Slide:
        return self._slides[slide_number]

    def get_all_slides(self):
        return self._slides

    def set_slide(self, slide_number: int, value: Slide):
        self._slides[slide_number] = value

    def get_slide_cnt(self):
        return len(self._slides)
