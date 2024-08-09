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
        files = [os.path.join(path, file) for file in sorted(os.listdir(path))]
        print(len(files))
        h, w = numpy.shape(cv2.imread(files[0], cv2.IMREAD_GRAYSCALE))[:2]
        print("heigh: ", h, " width: ", w)
        g = GeoFormer(w, 0.8, no_match_upscale=False, ckpt='saved_ckpt/geoformer.ckpt', device='cuda')
        video = cv2.VideoCapture(args.video, apiPreference=cv2.CAP_FFMPEG)
        video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
        print(video_duration)
        print(video.get(cv2.CAP_PROP_FPS))
        print(video)
        pos = 0.0
        while video.isOpened():
            newFrame, frame = video.read()
            print(video.get(cv2.CAP_PROP_POS_MSEC) / 1000)
            if newFrame:
                for file in files:
                    if file is None:
                        continue
                    matches, kpts1, kpts2, scores = g.match_pairs(frame, file, is_draw=False)
                    homo_checker.process(matches)
                    print('\r', matches.shape, file, end='')
                print("")
            print(homo_checker.get_homography_matrix())
            print("best correspondences: ", homo_checker.current_frame_homog_correspondences)
            print(pos)
            pos = pos + video_duration / 20
            if pos > video_duration:
                break
            print(video.set(cv2.CAP_PROP_POS_MSEC, pos))
        pos = 0
        for v in range(30):
            pos = pos + video_duration / 30
            if pos > video_duration:
                break
            print(video.set(cv2.CAP_PROP_POS_MSEC, pos))
            got_img, frame = video.read()
            if not got_img:
                continue
            newFrame = homo_checker.homog_transform(w, h, frame)
            cv2.imwrite(f"./data/imgs/{v}.png", newFrame)
        video.release()
