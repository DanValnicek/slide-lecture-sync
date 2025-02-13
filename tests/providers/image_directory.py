from pathlib import Path
from xml.etree.ElementTree import ElementTree
import cv2
import numpy as np

from . import DataProvider


class CVATXMLProvider(DataProvider):
    def __init__(self, image_dir, cvat_xml_path, presentation_path):
        self.image_dir = Path(image_dir)
        self.cvat_xml_path = Path(cvat_xml_path)
        self.presentation_pth = Path(presentation_path)

    @property
    def presentation_path(self) -> Path:
        return self.presentation_pth

    def test_cases(self) -> list[tuple[int, str]]:
        cases = []
        root = ElementTree(file=self.cvat_xml_path)
        # Iterate over each image element in the XML
        for image in root.findall('image'):
            # Get the 'name' attribute of the image
            filename = image.get('name')
            # Find the SlideNum attribute within the tag
            slide_num = image.find(".//tag[@label='Slide']/attribute[@name='SlideNum']").text
            # Add the (SlideNum, filename) tuple to the list
            cases.append((int(slide_num), filename))
        return cases

    def get_test_input(self, test_identifier: tuple[int, str]) -> tuple[int, np.ndarray]:
        if test_identifier[0] - 1 < 0:
            return None, cv2.imread(self.image_dir / test_identifier[1])
        return test_identifier[0] - 1, cv2.imread(self.image_dir / test_identifier[1])
