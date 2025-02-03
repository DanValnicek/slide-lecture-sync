import pathlib
from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class DataProvider(ABC):
    @property
    @abstractmethod
    def presentation_path(self) -> pathlib.Path:
        pass

    @abstractmethod
    def test_cases(self) -> Any:
        """Return some identifier of the data that needs to be used to get the right image."""
        pass

    def get_test_input(self, test_identifier: Any) -> tuple[int, np.ndarray]:
        pass
