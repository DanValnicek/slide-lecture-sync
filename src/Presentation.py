import logging
from abc import ABC
from pathlib import Path
from typing import List, Tuple

from PIL.Image import Image
from pymupdf import pymupdf


class PresentationCreator:
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
class PresentationSlide(ImageDecorator):
    def __init__(self, img: Image, page_number: int, presentation: "Presentation") -> None:
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
class Presentation(ABC):

    def get_slide(self, slide_number: int) -> PresentationSlide:
        ...

    def get_all_slides(self):
        ...

    def set_slide(self, slide_number: int, value: ImageDecorator):
        ...

    def get_slide_cnt(self):
        ...

    def __new__(cls, path: Path):
        # Dynamically assign class based on file extension
        if cls is Presentation:
            cls = PresentationCreator.get(path.suffix)
        return super().__new__(cls)

    def get_pdf_file_path(self):
        pass

    def __init__(self, path: Path):
        pass


# Register PdfPresentation for .pdf extension
@PresentationCreator.register('.pdf')
class PdfPresentation(Presentation):
    _slides: List[PresentationSlide]

    def __init__(self, path: Path):
        self.path = Path(path)
        # Convert PDF to list of images (one per page)
        slides = [page.get_pixmap(dpi=43).pil_image() for page in pymupdf.open(self.path)]
        self._slides = [PresentationSlide(img=img, page_number=i, presentation=self) for i, img in
                           enumerate(slides)]

        logging.getLogger(__name__).debug("file count: " + str(self.get_slide_cnt()))

    def get_pdf_file_path(self):
        return self.path

    def get_slide(self, slide_number: int) -> PresentationSlide:
        return self._slides[slide_number]

    def get_all_slides(self):
        return self._slides

    def set_slide(self, slide_number: int, value: PresentationSlide):
        self._slides[slide_number] = value

    def get_slide_cnt(self):
        return len(self._slides)
