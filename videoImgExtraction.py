import argparse
import os
import tempfile

import cv2
import numpy
from pdf2image import convert_from_path

from HomographyProcessor import HomographyProcessor
from inference import GeoFormer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract images from video')
    parser.add_argument('--video', '-v', type=str)
    parser.add_argument('--pdf', type=str)
    args = parser.parse_args()
    homo_checker = HomographyProcessor()
    print(args.pdf)
    with tempfile.TemporaryDirectory() as path:
        images_from_path = convert_from_path(args.pdf, output_file='pdf', fmt="jpg", output_folder=path,
                                             size=(720, None))

        # directory, _, file = next(os.walk(path, topdown=True, onerror=None, followlinks=False))
        # print(type(file[0]))
        # print(directory)
        # file = os.path.join(directory, file[4])
        # file = os.path.join(path, sorted(os.listdir(path))[0])
        files = [os.path.join(path, file) for file in sorted(os.listdir(path))]
        print(len(files))
        h, w = numpy.shape(cv2.imread(files[0], cv2.IMREAD_GRAYSCALE))[:2]

        print("heigh: ", h, " width: ", w)
        g = GeoFormer(w, 0.8, no_match_upscale=False, ckpt='saved_ckpt/geoformer.ckpt', device='cuda')
        # video = cv2.cudacodec.VideoCapture(args.video, apiPreference=cv2.CAP_FFMPEG)
        video = cv2.VideoCapture(args.video, apiPreference=cv2.CAP_FFMPEG)
        print(video.get(cv2.CAP_PROP_FPS))
        print(video)
        # img = './tmp/6b13a04a-73a9-41b5-8aef-a1d4dbdb1b78-01.tif'
        # img = './tmp/70c37ebe-257f-4553-91c4-75e2411bddd5-01.jpg'
        # img = './data/imgs/img.png'
        # cnt = 15
        cnt = 0
        pos = 0.0
        # video.set(cv2.CAP_PROP_POS_MSEC, 27 * 60 * 1000 + 14000)
        # video.set(cv2.CAP_PROP_POS_MSEC, 15000)
        while video.isOpened():
            # ret = video.grab()
            # if video.read():
            # if cnt <= video.get(cv2.CAP_PROP_POS_MSEC) / (10 * 60) * 1000:
            #     cnt = cnt + 1
            # _, frame = video.retrieve()
            newFrame, frame = video.read()
            print(video.get(cv2.CAP_PROP_POS_MSEC) / 1000)
            if newFrame:
                for file in files:
                    if file is None:
                        continue
                    matches, kpts1, kpts2, scores = g.match_pairs(frame, file, is_draw=False)
                    homo_checker.process(matches)

                    print('\r', matches.shape, file, end='')

                homo_checker.add_current_frame_and_start_new()
                print("")
            print(homo_checker.get_homography_matrix())
            # print(type(matches))
            # print(numpy.shape(matches))
            # print(matches)
            # h, mask = pydegensac.findHomography(matches[:, 2:4], matches[:, :2], 0.4)
            # print(homog)
            # for pixel in kpts1:
            #     frame[pixel[1].astype(int), pixel[0].astype(int)] = [255, 0, 0]
            # max_index = numpy.argmax(scores)
            # max_val = kpts2[max_index]
            # max_val = numpy.array([0, 0, 1])

            # ref_corners = numpy.array([[0, 0, 1], [w, 0, 1], [0, h, 1],
            #                            [w, h, 1]]).T  # Use actual width (w) and height (h) of reference image
            # transformed_corners = numpy.linalg.inv(homog) @ ref_corners
            # transformed_corners = transformed_corners / transformed_corners[2, :]
            # transformed_corners = transformed_corners[:2, :].T
            # print(transformed_corners)
            # pts = numpy.array(transformed_corners, numpy.int32)
            # frame = cv2.polylines(frame, [pts], False, (0, 255, 255))
            # plt.imshow(frame)
            # Mark the transformed corners on the frame
            # for corner in transformed_corners:
            #     if 0 <= corner[0] < frame.shape[1] and 0 <= corner[1] < frame.shape[0]:
            # frame[tuple(corner.astype(int))] = [0, 0, 255]
            # frame = cv2.circle(frame, tuple(corner.astype(int)), 5,
            #                    (0, 0, 255), -1)
            # plt.imshow(frame)
            # cv2.imwrite(f"./data/imgs/{cnt}.png", frame)
            print(pos)
            pos = pos + 150 * 60 * 1000 / 20
            if pos > 150 * 60 * 1000:
                break
            print(video.set(cv2.CAP_PROP_POS_MSEC, pos))
        # else:
        #     break
        # homog = numpy.matrix(
        #     '2.03867778e+00  4.67787567e-01  5.99155938e+02; -6.71261747e-03  1.75355807e+00  1.59732382e+01; 3.49173534e-04 4.41266821e-04 1.00000000e+00')
        for v in range(20):
            # video.set(cv2.CAP_PROP_POS_AVI_RATIO, v * random.random() / 20)
            pos = pos + 150 * 60 * 1000 / 30
            if pos > 150 * 60 * 1000:
                break
            print(video.set(cv2.CAP_PROP_POS_MSEC, pos))
            # read = False
            # while not read:
            pts = numpy.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            _, frame = video.read()
            # print(homog.shape)
            dst = cv2.perspectiveTransform(pts, homo_checker.get_homography_matrix())
            perspectiveM = cv2.getPerspectiveTransform(numpy.float32(dst), pts)
            newFrame = cv2.warpPerspective(frame, perspectiveM, (w, h))
            # frame = frame @ homo_checker.get_homography_matrix()
            cv2.imwrite(f"./data/imgs/{v}.png", newFrame)
        video.release()
