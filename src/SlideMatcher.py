import sys
from bisect import bisect
from collections import defaultdict
from typing import Sequence

import cv2
import numpy as np

from src import Presentation
from src.HomographyProcessor import HomographyProcessor


class SlideMatcher:
    video: cv2.VideoCapture
    presentation: Presentation
    # list of keypoint/descriptor indexes of the last
    last_slide_kp_idx: list
    descriptors: list
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, presentation: Presentation):
        self.matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        self.sift_detector = cv2.SIFT.create()
        self.flannIndex = None
        self.presentation = presentation
        self.last_slide_kp_idx = []
        self.keypoints = []
        self.descriptors = []

    def warp_and_recompute_slide_descriptors(self, frame, homog, slide_idx):
        warped_img = cv2.warpPerspective(frame, homog, self.presentation.slides[slide_idx].image.size)
        kp2, desc2 = self.sift_detector.compute(warped_img, self.slideKeypoints(slide_idx), None)
        slide_descriptors = self.slideDescriptors(slide_idx)
        matches = self.matcher.knnMatch(desc2, slide_descriptors, k=1)
        if len(matches) < 5:
            return
        dataset_keypoints = self.slideKeypoints(slide_idx)
        src_pts2 = np.float32([dataset_keypoints[m[0].trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts2 = np.float32([kp2[m[0].queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        homog2, mask2 = cv2.findHomography(dst_pts2, src_pts2, cv2.USAC_ACCURATE, 1.0)
        descriptors = [slide_descriptors[i] for i, inlier in enumerate(mask2) if inlier]
        return descriptors

    def pick_best_slide(self, matched_descriptors_from_all, slide_idxs):
        if slide_idxs == []:
            return None
        if len(slide_idxs) == 1:
            return slide_idxs[0]
        unique_descriptors = np.unique(np.vstack(matched_descriptors_from_all), axis=0)
        id_scores = []
        for slide_id in slide_idxs:
            matches = self.matcher.knnMatch(unique_descriptors, self.slideDescriptors(slide_id), k=1)
            distance = sum([1 if m[0].distance < 0.5 else 0 for m in matches])
            id_scores.append((slide_id, distance))
        max_match = max(id_scores, key=lambda x: x[1])
        pruned_scores = [val for val in id_scores if val[1] > max_match[1] * 0.9]
        return min(pruned_scores, key=lambda x: self.slideDescCnt(x[0]))[0]

    def detect_and_sort_descriptors_from_frame(self, frame):
        kp, desc = self.sift_detector.detectAndCompute(frame, None)
        matches = self.flannIndex.knnSearch(desc, 1)
        instance_cnt = defaultdict(list)
        for i, m in enumerate(matches[0]):
            index = self.descIdxToSlideIdx(m[0])
            instance_cnt[index].append((self.keypoints[m[0]].pt, kp[i].pt))
        return instance_cnt

    @staticmethod
    def spatial_pruning_and_verification(src_dst_kps, frame_h_w, slide_h_w):
        src_pts = np.float32([v[0] for v in src_dst_kps]).reshape(-1, 1, 2)
        dst_pts = np.float32([v[1] for v in src_dst_kps]).reshape(-1, 1, 2)
        homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.USAC_ACCURATE, 1.0)
        f_h, f_w, = frame_h_w
        s_h, s_w, = slide_h_w
        if homog is None or not HomographyProcessor.reasonableHomography(homog, f_w, f_h, s_w, s_h):
            return
        return homog

    def matched_slide(self, frame, debug_info: list = None):
        slides_keypoints = self.detect_and_sort_descriptors_from_frame(frame)
        match_histogram = dict()
        picked_descriptors = []
        picked_slides = []
        for slide_idx, src_dst_kps in slides_keypoints.items():
            if len(src_dst_kps) < 5:
                continue
            homog = self.spatial_pruning_and_verification(src_dst_kps, frame.shape[:2],
                                                          self.presentation.slides[slide_idx].image.size)
            if homog is None:
                continue
            calc_result = self.warp_and_recompute_slide_descriptors(frame, homog, slide_idx)
            if calc_result is None:
                continue
            picked_descriptors.append(calc_result)
            picked_slides.append(slide_idx)
            warped_img = cv2.warpPerspective(frame, homog, self.presentation.slides[slide_idx].image.size)
            if debug_info is not None and (debug_info is [] or len(debug_info) <= 3):
                if len(debug_info) == 3:
                    debug_info.pop(-1)
                best_keypoints1 = []
                best_keypoints2 = []
                # for i, m in enumerate(mask2):
                #     if m:
                #         best_keypoints2.append(cv2.KeyPoint(dst_pts2[i][0][0], dst_pts2[i][0][1], 1))
                #         best_keypoints1.append(cv2.KeyPoint(src_pts2[i][0][0], src_pts2[i][0][1], 1))
                # best_keypoints1 = [kp[m.queryIdx].pt for m in significant_kp]
                # best_keypoints2 = [self.keypoints[m.trainIdx].pt for m in significant_kp]
                debug_info.append({
                    'matched_slide': slide_idx,
                    'visual': cv2.drawMatches(
                        # frame,
                        warped_img,
                        # [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints1],
                        best_keypoints2,
                        np.array(self.presentation.slides[slide_idx].image)[:, :, ::-1],
                        # [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints2],
                        best_keypoints1,
                        [cv2.DMatch(i, i, 0) for i in range(len(best_keypoints1))],
                        None,
                        flags=cv2.DrawMatchesFlags_DEFAULT),
                    'homog': homog,
                    'warped_image': warped_img})
                # debug_info = sorted(debug_info,
                #                     key=lambda img_tup: match_histogram[img_tup['matched_slide']],
                #                     reverse=True)
        match_histogram[self.pick_best_slide(picked_descriptors, picked_slides)] = 1
        if match_histogram == {}:
            return match_histogram, None, None
        return match_histogram, max(match_histogram, key=match_histogram.get), debug_info

    def descIdxToSlideIdx(self, train_id):
        return bisect(self.last_slide_kp_idx, train_id)

    def slideDescriptors(self, slide_idx):
        return self.descriptors[slice(*self.slideIdxToDescRange(slide_idx))]

    def slideKeypoints(self, slide_idx):
        return self.keypoints[slice(*self.slideIdxToDescRange(slide_idx))]

    def slideIdxToDescRange(self, slide_idx) -> tuple[int, int]:
        if slide_idx == 0:
            return 0, self.last_slide_kp_idx[0]
        return self.last_slide_kp_idx[slide_idx - 1], self.last_slide_kp_idx[slide_idx]

    def slideDescCnt(self, slide_idx):
        if slide_idx == 0:
            return self.last_slide_kp_idx[0]
        return self.last_slide_kp_idx[slide_idx] - self.last_slide_kp_idx[slide_idx - 1]

    def create_training_keypoint_set(self):
        self.descriptors = []
        self.keypoints = []
        for slide in self.presentation.slides:
            kp, desc = (self.sift_detector.detectAndCompute(np.array(slide.image), None))
            self.descriptors.append(desc)
            self.keypoints += kp
            self.last_slide_kp_idx.append(len(self.keypoints))
        np.set_printoptions(threshold=sys.maxsize)
        self.descriptors = np.vstack(self.descriptors)
        self.flannIndex = cv2.flann.Index(self.descriptors, {"algorithm": 1, "trees": 5})
