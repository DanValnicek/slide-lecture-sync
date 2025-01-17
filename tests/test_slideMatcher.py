import os
import pathlib

import cv2
import numpy as np
import pytest
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfWriter

from src.Presentation import Presentation
from src.SlideMatcher import SlideMatcher
from tests.IDM_slides import IDM_testing

out_dir = os.path.join(pathlib.Path(__file__).parent.resolve(), "test_output/")


class FailureInfo:
    img: np.ndarray
    match_score_chart: dict
    expected_slide: int
    matched_slide: int

    def __init__(self, img, match_score_chart, expected_slide, matched_slide):
        self.img = img
        self.expected_slide = expected_slide
        self.match_score_chart = match_score_chart
        self.matched_slide = matched_slide


def create_failure_report_single_match(output_path, failure_info: FailureInfo):
    with PdfPages(output_path / f"slide{failure_info.expected_slide:03d}-report.pdf") as pdf:
        fig, axes = plt.subplots(2, 1, figsize=(10, 10))  # Two rows: image + bar chart
        axes = axes.ravel()  # Flatten axes for easier access

        # First row: Display the image
        if failure_info.img is None:
            axes[0].set_title("Couldn't match")
            axes[0].axis('off')  # Hide axes for no image
        else:
            axes[0].imshow(cv2.cvtColor(failure_info.img, cv2.COLOR_BGR2RGB), aspect='auto')
            axes[0].set_title(f"Expected Slide: {failure_info.expected_slide} | Got: {failure_info.matched_slide}")
            axes[0].axis('off')  # Hide axes for a cleaner look

        # Second row: Bar chart
        axes[1].bar(failure_info.match_score_chart.keys(), failure_info.match_score_chart.values(), align='center',
                    tick_label=[str(key) for key in failure_info.match_score_chart.keys()])
        axes[1].set_xlabel('Slide Number')
        axes[1].set_ylabel('Match Valuation')
        axes[1].set_title('Match Analysis')

        # Save the current page
        plt.tight_layout()
        pdf.savefig(fig)
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


passed = 0
total_test_cnt = 0


@pytest.fixture(scope="module")
def setup_idm_test():
    """
    Fixture to set up the necessary components for the IDM test.
    """
    test_data = IDM_testing()
    presentation = Presentation(test_data.presentation_path)
    video = cv2.VideoCapture(test_data.video_path)
    assert video.isOpened()

    slide_matcher = SlideMatcher(presentation)
    slide_matcher.create_training_keypoint_set()

    yield test_data, video, slide_matcher

    video.release()


@pytest.fixture(scope="module")
def test_tmp_dir(tmp_path_factory, request):
    tmp_dir = tmp_path_factory.mktemp("match_testing")
    yield tmp_dir
    create_failure_report(os.path.join(out_dir, request.module.__name__), tmp_dir, passed, total_test_cnt)


@pytest.mark.parametrize("slide_n, stamp", IDM_testing().get_slide_with_timestamp())
def test_slide_matcher_on_idm(setup_idm_test, slide_n, stamp, test_tmp_dir):
    """
    Parametrized test for slide matcher on IDM data.
    """
    test_data, video, slide_matcher = setup_idm_test

    video.set(cv2.CAP_PROP_POS_MSEC, stamp)
    got_img, frame = video.read()
    if not got_img:
        pytest.fail(f"Failed to read frame at timestamp {stamp} ms")

    hist, best_slide, img = slide_matcher.matched_slide(frame)
    global total_test_cnt
    total_test_cnt += 1
    try:
        assert best_slide == slide_n
        global passed
        passed += 1
    except AssertionError:
        create_failure_report_single_match(
            test_tmp_dir,
            FailureInfo(
                img,
                {key: hist[key] for key in sorted(hist)},
                slide_n,
                best_slide
            )
        )
        raise
