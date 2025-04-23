import pathlib
from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class DataProvider(ABC):
    @property
    def get_test_suite_name(self):
        ...

    @property
    @abstractmethod
    def presentation_path(self) -> pathlib.Path:
        pass

    @property
    def get_test_cnt(self):
        ...

    @abstractmethod
    def test_cases(self) -> Any:
        """Return some identifier of the test_data that needs to be used to get the right image."""
        pass

    def get_test_input(self, test_identifier: Any) -> tuple[int, np.ndarray]:
        pass
