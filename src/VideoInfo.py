from pypdf import PdfWriter
from pypdf.generic import ArrayObject, NameObject, DictionaryObject

from src.Presentation import ImageDecorator, Presentation


class SlideIntervalInfo(ImageDecorator):
    def __init__(self, image):
        super().__init__(image)
        self.intervals: list[list[int, int]] = []

    def add_point_in_time(self, time_ms):
        for i, interval in enumerate(self.intervals):
            start, end = interval
            if abs(time_ms - end) <= 1000:
                self.intervals[i][1] = time_ms
                return
            if abs(start - time_ms) <= 1000:
                self.intervals[i][0] = time_ms
                return
            if start <= time_ms <= end:
                return
        self.intervals.append([time_ms, time_ms])

    def get_intervals(self):
        self.intervals.sort(key=lambda x: x[0])
        i = 0
        while i < len(self.intervals) - 1:
            if self.intervals[i + 1][0] <= self.intervals[i][0] <= self.intervals[i + 1][1]:
                self.intervals[i][1] = self.intervals[i + 1][1]
                self.intervals.pop(i + 1)
            else:
                i += 1
        return self.intervals


class PresentationWSlideIntervals:
    def __init__(self, presentation: Presentation):
        self.presentation: Presentation = presentation
        for i, slide in enumerate(presentation.get_all_slides()):
            if not isinstance(slide, SlideIntervalInfo):
                presentation.set_slide(i, SlideIntervalInfo(slide))

    def __getattr__(self, name):
        return getattr(self.presentation, name)

    def add_point_to_slides(self, slide_n, time_ms):
        if slide_n is None:
            return
        self.presentation.get_slide(slide_n).add_point_in_time(time_ms)

    def compile_pdf_w_timestamps(self):
        orig_pdf_path = self.presentation.get_pdf_file_path()
        writer = PdfWriter("new.pdf", orig_pdf_path)
        for i, slide in enumerate(self.presentation.get_all_slides()):
            writer.pages[i][NameObject("/DANV_SlideVideoSync")] = DictionaryObject(
                {NameObject("/SlideAppearanceIntervals"): ArrayObject(slide.get_intervals())}
            )
        with open("slides_with_specific_timing.pdf", "wb") as f:
            writer.write(f)
