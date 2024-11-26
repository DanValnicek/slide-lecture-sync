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
# def create_failure_report(output_path, failure_data, passed):
#     # cols = 2
#     cols = 1
#     # plt.suptitle(f"count: {passed}, failed:{len(failure_data)}", fontsize=16, fontweight='bold', y=0.99)
#     # axes[0].imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
#     # for i, img in enumerate(failure_data):
#     with PdfPages(output_path) as pdf:
#         plt.title(f"count: {passed}, failed:{len(failure_data)}", fontsize=16, fontweight='bold', y=0.99)
#         fig, axes = plt.subplots(len(failure_data) * 2, cols, figsize=(10, 8 * 2), dpi=100)
#         axes = axes.ravel()  # Flatten axes for easier iteration
#         for i in range(0, len(failure_data) * 2, 2):
#             img = failure_data[i // 2]
#             if img[0] is None:
#                 axes[i * cols].set_title("Couldn't match")
#                 continue
#             axes[i * cols].axis('off')
#             axes[i * cols].set_title(f"expected slide: {img[2]} got: {img[3]}")
#             axes[i * cols].imshow(cv2.cvtColor(img[0], cv2.COLOR_BGR2RGB), aspect='auto')
#             # axes[i * 2].set_title(f"slide: {img[3]}\nat: {img[2]}\nmatch_cnt: {img[4]}\nmatched_slides_cnt: {img[5]}")
#             # axes[i * cols + 1].imshow(img[1])
#             axes[i * cols + 1].bar(img[1].keys(), img[1].values(), align='center',
#                                    tick_label=[str(key) for key in img[1].keys()])
#             axes[i * cols + 1].set_xlabel('Slide number')
#             axes[i * cols + 1].set_ylabel('match valuation')
#             plt.tight_layout()
#             pdf.savefig(fig)
#             plt.close(fig)
#

@pytest.fixture(scope="session", autouse=True)
def generate_failure_report_at_end():
    """Generate a single PDF with all failures at the end of the test session."""
    yield  # Run tests first

    if failure_data:  # Only generate if there are failures
        output_path = os.path.join(os.getcwd(), "failure_report.pdf")
        create_failure_report(output_path, failure_data, passed)
        print(f"Failure report generated at: {output_path}")


passed = 0


def test_slide_matcher_on_IDM():
    test_data = IDM_testing()
    # assert os.path.exists(test_data.video_path)
    print(test_data.video_path)
    presentation = Presentation(test_data.presentation_path)
    video = cv2.VideoCapture(test_data.video_path)
    assert video.isOpened()
    slide_matcher = SlideMatcher(presentation)
    slide_matcher.create_training_keypoint_set()
    global passed
    for slide_n, stamp in test_data.get_slide_with_timestamp():
        try:
            passed = passed + 1
            video.set(cv2.CAP_PROP_POS_MSEC, stamp)
            got_img, frame = video.read()
            if not got_img:
                continue
            hist, best_slide, img = slide_matcher.matched_slide(frame)
            assert best_slide == slide_n
        except AssertionError:
            failure_data.append((img, {key: hist[key] for key in sorted(hist)}, slide_n, best_slide))
            pass
        except Exception as e:
            raise
    video.release()
    assert failure_data == []
