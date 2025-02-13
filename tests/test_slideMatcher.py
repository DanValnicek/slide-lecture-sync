import os
from pathlib import Path

import cv2
import pytest
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfWriter

from src.Presentation import Presentation
from .providers import *
from src.SlideMatcher import SlideMatcher

out_dir = os.path.join(Path(__file__).parent.resolve(), "test_output/")


class FailureInfo:
    images: list
    match_score_chart: dict
    expected_slide: int
    matched_slide: int

    def __init__(self, matched_images, match_score_chart, expected_slide, matched_slide):
        self.images = matched_images
        self.expected_slide = expected_slide
        self.match_score_chart = match_score_chart
        self.matched_slide = matched_slide


def create_failure_report_single_match(output_path, failure_info: FailureInfo):
    with PdfPages(output_path / f"slide{failure_info.expected_slide:03d}-report.pdf") as pdf:
        fig, axes = plt.subplots(1, 1, figsize=(10, 10))  # Two rows: image + bar chart
        axes.bar(failure_info.match_score_chart.keys(), failure_info.match_score_chart.values(), align='center',
                 tick_label=[str(key) for key in failure_info.match_score_chart.keys()])
        axes.set_xlabel('Slide Number')
        axes.set_ylabel('Match Valuation')
        axes.set_title(f"Expected Slide: {failure_info.expected_slide} | Got: {failure_info.matched_slide}")

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
            axes.imshow(cv2.cvtColor(data['warped_image'], cv2.COLOR_BGR2RGB), aspect='auto')
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
            fig, axes = plt.subplots(1, 1, figsize=(5, 5))  # Two rows: image + bar chart
            axes.table(
                cellText=data['homog2'],
                cellLoc='center',
                loc='center'
            )
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)  # Close figure to free up memory


def create_failure_report(output_path, tmp_out_dir, passed, total_test_count):
    # Initialize the PDF
    title_pdf_name = "_Title.pdf"  # underscore to make it first in sorted list
    with PdfPages(tmp_out_dir / title_pdf_name) as pdf:
        # Add a title page with the summary
        plt.figure(figsize=(10, 5))
        plt.text(0.5, 0.5, f"Count: {total_test_count}\nFailed: {total_test_count - passed}",
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


data_path = Path(__file__).parent / Path('data')
providers = [
    IDMVideoProvider(),
    CVATXMLProvider(data_path / 'IPK_test_imgs', data_path / 'annotations.xml',
                    data_path / 'IPK2023-24L-07-MULTICAST.pdf')
]


def pytest_generate_tests(metafunc):
    if "slide_matching_test" in metafunc.fixturenames:
        test_cases = []
        for provider in providers:
            try:
                test_cases.extend([(provider, case) for case in provider.test_cases()])
            except Exception as e:
                pytest.skip(f"Provider {type(provider).__name__} failed: {str(e)}")

        metafunc.parametrize("slide_matching_test", test_cases)


passed = 0
total_test_cnt = 0


@pytest.fixture(scope="module")
def test_tmp_dir(tmp_path_factory, request):
    tmp_dir = tmp_path_factory.mktemp("match_testing")
    yield tmp_dir
    create_failure_report(os.path.join(out_dir, request.module.__name__), tmp_dir, passed, total_test_cnt)


slide_matcher = None


def setup_matcher(data_provider: DataProvider):
    global slide_matcher
    presentation_path = data_provider.presentation_path
    if slide_matcher is None or slide_matcher[0] != presentation_path:
        slide_matcher = (presentation_path, SlideMatcher(Presentation(presentation_path)))
        slide_matcher[1].create_training_keypoint_set()
    return slide_matcher[1]


def test_slide_matcher(slide_matching_test, test_tmp_dir):
    provider, test = slide_matching_test
    slide_matcher = setup_matcher(provider)
    slide_n, frame = (provider.get_test_input(test))
    hist, best_slide, debug_data = slide_matcher.matched_slide(frame, [])
    global total_test_cnt
    total_test_cnt += 1
    try:
        assert best_slide == slide_n
        global passed
        passed += 1
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
        create_failure_report_single_match(
            test_tmp_dir,
            FailureInfo(
                debug_data,
                {key: hist[key] for key in sorted(hist)},
                slide_n,
                best_slide
            )
        )
        raise
