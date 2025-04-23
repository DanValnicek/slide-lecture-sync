import os
from pathlib import Path

import cv2
import pytest
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfWriter

from src.Presentation import Presentation
from src.SlideMatcher import SlideMatcher
from .providers import IntervalVideoProvider, DataProvider, CVATXMLProvider, IDMVideoProvider

out_dir = os.path.join(Path(__file__).parent.resolve(), "test_output/")


class FailureInfo:
    images: list
    match_score_chart: dict
    expected_slide: int
    matched_slide: int

    def __init__(self, matched_images, match_score_chart, expected_slide, matched_slide, test_suite):
        self.images = matched_images
        self.expected_slide = expected_slide
        self.match_score_chart = match_score_chart
        self.matched_slide = matched_slide
        self.test_suite = test_suite


test_data_path = Path(__file__).parent / Path('test_data')
data_path = Path(__file__).parents[1] / Path('data')
videos_path = data_path / Path("videos")
pdfs_path = data_path / Path("pdfs")
providers = [
    IDMVideoProvider(),
    CVATXMLProvider(test_data_path / 'IPK_test_imgs',
                    test_data_path / 'annotations.xml',
                    test_data_path / 'IPK2023-24L-07-MULTICAST.pdf'),
    IntervalVideoProvider(test_data_path / 'INP.json',
                          videos_path / "INP_2023-10-24_1080p.mp4",
                          pdfs_path / 'inp2023_06alu.pdf'),
    IntervalVideoProvider(test_data_path / 'IOS.json',
                          videos_path / "IOS_2023-02-22_1080p.mp4",
                          pdfs_path / "ios-prednaska-03.pdf"),
    IntervalVideoProvider(test_data_path / 'IDM.json',
                          videos_path / "IDM_2023-11-07_1080p.mp4",
                          pdfs_path / "grafy1.pdf"),
    IntervalVideoProvider(test_data_path / 'PIS.json',
                          videos_path / "PIS_objektovy_model2.mp4",
                          pdfs_path / "PIS_objektovy_model_dat.pdf"),
    IntervalVideoProvider(test_data_path / 'IPK.json',
                          videos_path / "IPK_2024-04-04_1080p.mp4",
                          pdfs_path / "IPK2023-24L-07-MULTICAST.pdf"),
]


def pytest_generate_tests(metafunc):
    if "slide_matching_test" in metafunc.fixturenames:
        provider = metafunc.cls.provider
        # test_cases = []
        try:
            test_cases = [(provider, case) for case in provider.test_cases()]
        except Exception as e:
            pytest.skip(f"Provider {type(provider).__name__} failed: {str(e)}")

        metafunc.parametrize("slide_matching_test", test_cases)


# passed = 0
# failed = 0

slide_matcher = None


class BaseSlideMatcherTest:
    provider: DataProvider = None  # will be set later
    failed: int
    passed: int

    @classmethod
    def setup_class(cls):
        cls.passed = 0
        cls.failed = 0

    # passed_cnt = 0

    # slide_matcher = None

    def create_failure_report_single_match(self, output_path, failure_info: FailureInfo):
        if failure_info.expected_slide is None:
            failure_info.expected_slide = -1
        if failure_info.matched_slide is None:
            failure_info.matched_slide = -1
        with PdfPages(
                output_path / f"{failure_info.test_suite}_fail{self.failed}_slide{failure_info.expected_slide:03d}-report.pdf") as pdf:
            fig, axes = plt.subplots(1, 1, figsize=(10, 10))  # Two rows: image + bar chart
            axes.bar(failure_info.match_score_chart.keys(), failure_info.match_score_chart.values(), align='center',
                     tick_label=[str(key) for key in failure_info.match_score_chart.keys()])
            axes.set_xlabel('Slide Number')
            axes.set_ylabel('Match Valuation')
            axes.set_title(
                f"suite: {failure_info.test_suite} Expected Slide: {failure_info.expected_slide} | Got: {failure_info.matched_slide}")

            # Save the current page
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)  # Close figure to free up memory

            for data in failure_info.images:
                fig, axes = plt.subplots(1, 1, figsize=(10, 10))  # Two rows: image + bar chart
                axes.imshow(cv2.cvtColor(data['visual'], cv2.COLOR_BGR2RGB), aspect='auto')
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)  # Close figure to free up memory
                fig, axes = plt.subplots(1, 1, figsize=(10, 10))  # Two rows: image + bar chart
                axes.imshow(data['warped_image'], aspect='auto')
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)  # Close figure to free up memory
                fig, axes = plt.subplots(1, 1, figsize=(5, 5))  # Two rows: image + bar chart
                axes.table(
                    cellText=data['homog'],
                    cellLoc='center',
                    loc='center'
                )
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)  # Close figure to free up memory
                # fig, axes = plt.subplots(1, 1, figsize=(5, 5))  # Two rows: image + bar chart
                # axes.table(
                #     cellText=test_data['homog2'],
                #     cellLoc='center',
                #     loc='center'
                # )
                # plt.tight_layout()
                # pdf.savefig(fig, bbox_inches='tight')
                # plt.close(fig)  # Close figure to free up memory

    def create_failure_report(self, output_path, tmp_out_dir):
        # Initialize the PDF
        title_pdf_name = "!Title.pdf"  # underscore to make it first in sorted list
        with PdfPages(tmp_out_dir / title_pdf_name) as pdf:
            # Add a title page with the summary
            plt.figure(figsize=(10, 5))
            plt.text(0.5, 0.5,
                     f"Count: {self.provider.get_test_cnt()}\nFailed: {self.failed}\nPassed: {self.passed}",
                     fontsize=20, ha='center', va='center', fontweight='bold')
            plt.axis('off')  # Remove axes for a clean title page
            pdf.savefig()
            plt.close()
        pdfs_to_merge = [os.path.join(tmp_out_dir, pdf) for pdf in os.listdir(tmp_out_dir) if pdf.endswith(".pdf")]
        pdfs_to_merge = sorted(pdfs_to_merge)
        merger = PdfWriter()
        for pdf in pdfs_to_merge:
            merger.append(pdf)
        with open(output_path + '.pdf', 'wb') as f:
            merger.write(f)

    @pytest.fixture(scope="class")
    def test_tmp_dir(self, tmp_path_factory, request):
        tmp_dir = tmp_path_factory.mktemp("match_testing")
        yield tmp_dir
        self.create_failure_report(os.path.join(out_dir, self.provider.get_test_suite_name()), tmp_dir)

    def setup_matcher(self, data_provider: DataProvider):
        presentation_path = data_provider.presentation_path
        global slide_matcher
        if slide_matcher is None or slide_matcher.presentation.get_pdf_file_path() != presentation_path:
            slide_matcher = SlideMatcher(Presentation(presentation_path))
            slide_matcher.create_training_keypoint_set()
        return slide_matcher

    def test_slide_matcher(self, slide_matching_test, test_tmp_dir):
        provider, test = slide_matching_test
        slide_match = self.setup_matcher(provider)
        slide_n, frame = (provider.get_test_input(test))
        hist, best_slide, debug_data = slide_match.matched_slide(frame, [])
        try:
            assert best_slide == slide_n
            type(self).passed += 1
            # cv2.imwrite("idk.png", debug_data[0]['visual'])
            # create_failure_report_single_match(
            #     test_tmp_dir,
            #     FailureInfo(
            #         debug_data,
            #         {key: hist[key] for key in sorted(hist)},
            #         slide_n,
            #         best_slide
            #     )
            # )
        except AssertionError:
            type(self).failed += 1
            self.create_failure_report_single_match(
                test_tmp_dir,
                FailureInfo(
                    debug_data,
                    {key: hist[key] for key in sorted(hist)},
                    slide_n,
                    best_slide,
                    provider.get_test_suite_name()
                )
            )
            raise


for provider in providers:
    name = f"TestSlideMatcher_{provider.get_test_suite_name()}"
    globals()[name] = type(name, (BaseSlideMatcherTest,), {"provider": provider})
