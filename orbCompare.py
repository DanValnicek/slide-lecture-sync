import logging

import cv2 as cv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

matching_plots = []
img1 = cv.imread('data/imgs/8-slide.png', cv.IMREAD_GRAYSCALE)  # queryImage
img2 = cv.imread('data/imgs/this.png', cv.IMREAD_GRAYSCALE)  # trainImage
print(img1)
print(img2)
if img1 is None:
    logging.log(logging.ERROR, "bad img file: " + img1)
    exit()
if img2 is None:
    logging.log(logging.ERROR, "bad img file: " + img2)
    exit()
# Initiate SIFT detector
sift = cv.ORB.create()
bfm = cv.BFMatcher(cv.NORM_HAMMING2, crossCheck=True)
# find the keypoints and descriptors with SIFT
x_step = img1.shape[1] // 5
y_step = img1.shape[0] // 5
y = 0
count = 0
x_c, y_c = 0, 0
while y < img1.shape[0]:
    y += y_step
    x = 0
    x_c = 0
    y_c += 1
    while x < img1.shape[1]:
        x += x_step
        count += 1
        x_c += 1
        print("xc: ", x_c, "yc: ", y_c)
        print("x: ", x, "y: ", y)
        print(img1.shape)
        section1 = img1[y - y_step:y - 1, x - x_step:x - 1]
        section2 = img2[y - y_step:y - 1, x - x_step:x - 1]
        kp1, des1 = sift.detectAndCompute(section1, None)
        kp2, des2 = sift.detectAndCompute(section2, None)
        # if des1 is None or des2 is None:
        #     print("skip")
        #     x += x_step
        #     continue
        # FLANN parameters
        # FLANN_INDEX_LSH = 6
        # index_params = dict(algorithm=FLANN_INDEX_LSH,
        #                     table_number=6,  # 12
        #                     key_size=12,  # 20
        #                     multi_probe_level=1)  # 2
        # search_params = dict(checks=50)  # or pass empty dictionary
        # flann = cv.FlannBasedMatcher(index_params, search_params)
        # matches = flann.knnMatch(des1, des2, k=2)
        matches = bfm.match(des1, des2)
        # Need to draw only good matches, so create a mask
        # ratio test as per Lowe's paper
        # broken = False
        # for i, match in enumerate(matches):
        #     if len(match) < 2:
        #         print("skip")
        #         x += x_step
        #         break
        #     if match[0].distance < 0.6 * match[1].distance:
        #         matchesMask[i] = [1, 0]
        draw_params = dict(matchColor=(0, 255, 0),
                           singlePointColor=(255, 0, 0),
                           # matchesMask=matchesMask,
                           flags=cv.DrawMatchesFlags_DEFAULT)
        img3 = cv.drawMatches(section1, kp1, section2, kp2, matches, None, **draw_params)
        matching_plots.append(img3)
print("count: ", count)
# n_rows = len(matching_plots) // 2 + len(matching_plots) % 2 + 1  # Calculate rows to fit all images
fig, axes = plt.subplots(len(matching_plots) + 1, 1, figsize=(10, 5 * len(matching_plots)))
axes = axes.ravel()  # Flatten axes for easier iteration

axes[0].imshow(cv.cvtColor(img1, cv.COLOR_BGR2RGB))
for i, img in enumerate(matching_plots):
    axes[i + 1].imshow(img)
    # axes[i].axis('off')  # Turn off axis labels for clarity

plt.tight_layout()
with PdfPages('data/imgs/matching.pdf') as pdf:
    pdf.savefig(fig)
plt.close()
