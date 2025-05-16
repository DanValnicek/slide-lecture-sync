# author Dan Valníček
# Annotation provider for IPK lecture implemented by having a folder full of images with annotations stored in xml file
# in the CVAT format.
# The annotations were made using the CVAT platform for image annotations.
# This is the second method used during development.
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
        self.test_cnt = 0

    def get_test_suite_name(self):
        return self.presentation_pth.stem + "xml_annot"

    def get_test_cnt(self):
        return self.test_cnt

    @property
    def presentation_path(self) -> Path:
        return self.presentation_pth

    def test_cases(self) -> list[tuple[int, str]]:
        cases = []
        root = ElementTree(file=self.cvat_xml_path)
        for image in root.findall('image'):
            filename = image.get('name')
            slide_num = image.find(".//tag[@label='Slide']/attribute[@name='SlideNum']").text
            cases.append((int(slide_num), filename))
        self.test_cnt = len(cases)
        return cases

    def get_test_input(self, test_identifier: tuple[int, str]) -> tuple[int, np.ndarray]:
        if test_identifier[0] - 1 < 0:
            return None, cv2.imread(self.image_dir / test_identifier[1])
        return test_identifier[0] - 1, cv2.imread(self.image_dir / test_identifier[1])
