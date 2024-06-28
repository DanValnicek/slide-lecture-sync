import argparse

import cv2
import numpy
import pydegensac
from matplotlib import pyplot as plt

from inference import GeoFormer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract images from video')
    parser.add_argument('--video', '-v', type=str)
    args = parser.parse_args()
    g = GeoFormer(1080, 0.4, no_match_upscale=False, ckpt='saved_ckpt/geoformer.ckpt', device='cuda')
    # video = cv2.cudacodec.VideoCapture(args.video, apiPreference=cv2.CAP_FFMPEG)
    video = cv2.VideoCapture(args.video, apiPreference=cv2.CAP_FFMPEG)
    print(video.get(cv2.CAP_PROP_FPS))
    print(video)
    h, w = numpy.shape(cv2.imread('./data/imgs/img.png'))[:2]
    cnt = 1620
    # cnt = 0
    video.set(cv2.CAP_PROP_POS_MSEC, 27 * 60 * 1000 + 14000)
    while video.isOpened():
        ret = video.grab()
        if ret:
            if cnt <= video.get(cv2.CAP_PROP_POS_MSEC) / 1000:
                _, frame = video.retrieve()
                print(video.get(cv2.CAP_PROP_POS_MSEC) / 1000)
                matches, kpts1, kpts2, scores = g.match_pairs(frame, './data/imgs/img.png', is_draw=False)
                homog, mask = pydegensac.findHomography(matches[:, :2], matches[:, 2:4], 0.4)
                # h, mask = pydegensac.findHomography(matches[:, 2:4], matches[:, :2], 0.4)

                for pixel in kpts1:
                    frame[pixel[1].astype(int), pixel[0].astype(int)] = [255, 0, 0]
                # max_index = numpy.argmax(scores)
                # max_val = kpts2[max_index]
                # max_val = numpy.array([0, 0, 1])

                ref_corners = numpy.array([[0, 0, 1], [w, 0, 1], [0, h, 1],
                                           [w, h, 1]]).T  # Use actual width (w) and height (h) of reference image
                transformed_corners = numpy.linalg.inv(homog) @ ref_corners
                transformed_corners = transformed_corners / transformed_corners[2, :]
                transformed_corners = transformed_corners[:2, :].T
                print(transformed_corners)
                pts = numpy.array(transformed_corners,numpy.int32)

                frame = cv2.polylines(frame, [pts], True, (0, 255, 255))
                plt.imshow(frame)
                # Mark the transformed corners on the frame
                # for corner in transformed_corners:
                #     if 0 <= corner[0] < frame.shape[1] and 0 <= corner[1] < frame.shape[0]:
                #         frame[tuple(corner.astype(int))] = [0,0,255]
                #         frame = cv2.circle(frame, tuple(corner.astype(int)), 5, (0, 0, 255), -1)

                # cv2.imwrite(f"./data/imgs/{cnt}.png", frame)
                print(matches.size)
                print(scores.size)
                print(kpts1.size)
                print(kpts2.size)
                print(h)
                cnt = cnt + 1
        else:
            break

    video.release()
