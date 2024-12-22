import os
import pathlib

import cv2
import pytest
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from src.Presentation import Presentation
from src.SlideMatcher import SlideMatcher
from tests.IDM_slides import IDM_testing

failure_data = []
out_dir = os.path.join(pathlib.Path(__file__).parent.resolve(), "test_output/")


def create_failure_report(output_path, failure_data, passed):
    # Initialize the PDF
    with PdfPages(output_path) as pdf:
        # Add a title page with the summary
        plt.figure(figsize=(10, 5))
        plt.text(0.5, 0.5, f"Count: {passed}\nFailed: {len(failure_data)}",
                 fontsize=20, ha='center', va='center', fontweight='bold')
        plt.axis('off')  # Remove axes for a clean title page
        pdf.savefig()
        plt.close()

        # Generate a page for each failure
        for img in failure_data:
            fig, axes = plt.subplots(2, 1, figsize=(10, 10))  # Two rows: image + bar chart
            axes = axes.ravel()  # Flatten axes for easier access

            # First row: Display the image
            if img[0] is None:
                axes[0].set_title("Couldn't match")
                axes[0].axis('off')  # Hide axes for no image
            else:
                axes[0].imshow(cv2.cvtColor(img[0], cv2.COLOR_BGR2RGB), aspect='auto')
                axes[0].set_title(f"Expected Slide: {img[2]} | Got: {img[3]}")
                axes[0].axis('off')  # Hide axes for a cleaner look

            # Second row: Bar chart
            axes[1].bar(img[1].keys(), img[1].values(), align='center',
                        tick_label=[str(key) for key in img[1].keys()])
            axes[1].set_xlabel('Slide Number')
            axes[1].set_ylabel('Match Valuation')
            axes[1].set_title('Match Analysis')

            # Save the current page
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)  # Close figure to free up memory


# @pytest.fixture(scope="session", autouse=True)
# def generate_failure_report_at_end():
#     """Generate a single PDF with all failures at the end of the test session."""
#     yield  # Run tests first
#     if failure_data:  # Only generate if there are failures
#         output_path = os.path.join(os.getcwd(), "failure_report.pdf")
#         create_failure_report(output_path, failure_data, passed)
#         print(f"Failure report generated at: {output_path}")
#
#
passed = 0


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

@pytest.mark.parametrize("slide_n, stamp", IDM_testing().get_slide_with_timestamp())
def test_slide_matcher_on_idm(setup_idm_test, slide_n, stamp):
    """
    Parametrized test for slide matcher on IDM data.
    """
    test_data, video, slide_matcher = setup_idm_test

    video.set(cv2.CAP_PROP_POS_MSEC, stamp)
    got_img, frame = video.read()
    if not got_img:
        pytest.fail(f"Failed to read frame at timestamp {stamp} ms")

    hist, best_slide, img = slide_matcher.matched_slide(frame)

    try:
        assert best_slide == slide_n
    except AssertionError:
        raise
        # failure_data.append((img, {key: hist[key] for key in sorted(hist)}, slide_n, best_slide))

    assert not failure_data, f"Failures detected: {failure_data}"