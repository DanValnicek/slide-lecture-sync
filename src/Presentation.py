import logging
import tempfile
from abc import ABC
from pathlib import Path
from typing import List, Tuple

from PIL.Image import Image
from pdf2image import convert_from_path


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
        self._image = img

    @property
    def image(self) -> Image:
        return self._image

    def __getattr__(self, method_name):
        """Delegate method calls to the wrapped image."""
        return getattr(self._image, method_name)


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
    slides: List[PresentationSlide]

    def __new__(cls, path: Path):
        # Dynamically assign class based on file extension
        if cls is Presentation:
            cls = PresentationCreator.get(path.suffix)
        return super().__new__(cls)

    def __init__(self, path: Path):
        pass


# Register PdfPresentation for .pdf extension
@PresentationCreator.register('.pdf')
class PdfPresentation(Presentation):

    def __init__(self, path: Path):
        # Convert PDF to list of images (one per page)
        with tempfile.TemporaryDirectory() as temp_dir:
            slides = convert_from_path(path, output_file='pdf', fmt="ppm", output_folder=temp_dir, size=(720, None))
            self.slides = [PresentationSlide(img=img, page_number=i, presentation=self) for i, img in enumerate(slides)]
        logging.getLogger(__name__).debug("file count: " + str(len(self.slides)))
