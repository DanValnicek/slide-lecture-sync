import sys
from bisect import bisect
from collections import defaultdict
from typing import Sequence

import cv2
import numpy as np

from src import Presentation


class SlideMatcher:
    video: cv2.VideoCapture
    presentation: Presentation
    # list of keypoint/descriptor indexes of the last
    last_slide_kp_idx: list
    descriptors: np.ndarray
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, presentation: Presentation):
        self.weights = []
        self.keypoint_clusters = None
        self.presentation = presentation
        self.last_slide_kp_idx = []
        self.keypoints = []
        self.descriptors = []

    # def matchPresentationToVideo(self):
    @staticmethod
    def eval_keypoints_by_distance(src_keypoint1: cv2.KeyPoint, dst_keypoint2: cv2.KeyPoint) -> float:
        """https://www.desmos.com/calculator/9ag3brj92d"""
        distance = np.linalg.norm(src_keypoint1 - dst_keypoint2)
        if distance > 7.0:
            return 0.0
        return np.exp(-(distance ** 2) / (2 * 3 ** 2))

    def matched_slide(self, frame) -> (int, int):
        matcher = cv2.SIFT.create()

        kp, desc = matcher.detectAndCompute(frame, None)
        bfm = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        matches = bfm.knnMatch(desc, self.descriptors, k=1)
        instance_cnt = defaultdict(list)

        for m in matches:
            index = bisect(self.last_slide_kp_idx, m[0].trainIdx)
            instance_cnt[index].append(m[0])

        match_histogram = dict()
        best_slide = None
        max_eval_sum = -1
        best_keypoints1 = []
        best_keypoints2 = []

        for slide_idx, slide_matches in sorted(instance_cnt.items(), key=lambda x: len(x[1]), reverse=True):
            # kps_lower_idx = self.last_slide_kp_idx[slide_idx - 1] if slide_idx != 0 else 0
            # kps_upper_idx = self.last_slide_kp_idx[slide_idx]
            if len(slide_matches) < 4:
                continue

            weights = [self.weights[m.trainIdx] for m in slide_matches]
            src_pts = np.float32([self.keypoints[m.trainIdx].pt for m in slide_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp[m.queryIdx].pt for m in slide_matches]).reshape(-1, 1, 2)

            homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
            if homog is None:
                continue

            transformed_pts = cv2.perspectiveTransform(dst_pts, homog)
            eval_sum = 0.0
            for i in range(len(transformed_pts)):
                # eval_sum += self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i])
                eval_sum += self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i]) * weights[i]

            # slide_desc_cnt = (self.last_slide_kp_idx[slide_idx] -
            #                   (self.last_slide_kp_idx[slide_idx - 1] if slide_idx != 0 else 0))
            # match_score = eval_sum / slide_desc_cnt
            match_score = eval_sum
            match_histogram[slide_idx] = match_score

            if match_score > max_eval_sum:
                max_eval_sum = match_score
                best_slide = slide_idx
                best_keypoints1 = [kp[m.queryIdx].pt for m in slide_matches]
                best_keypoints2 = [self.keypoints[m.trainIdx].pt for m in slide_matches]
        result_img = None
        if best_slide is not None:
            result_img = cv2.drawMatches(
                frame,
                [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints1],
                np.array(self.presentation.slides[best_slide].image)[:, :, ::-1],
                [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints2],
                [cv2.DMatch(i, i, 0) for i in range(len(best_keypoints1))],
                None,
                flags=cv2.DrawMatchesFlags_DEFAULT
            )
            # cv2.imwrite(f"./data/imgs/{best_slide}_w{frame_time}.png", result_img)
        if match_histogram == {}:
            return match_histogram, None, None
        return match_histogram, max(match_histogram, key=match_histogram.get), result_img

    @staticmethod
    def count_same_descriptors(desc_query_results):
        similar_descriptor_counts = dict()
        for descriptor in desc_query_results:
            for i in range(0, len(descriptor)):
                if descriptor[i].queryIdx == descriptor[i].trainIdx:
                    continue
                if descriptor[i].distance > 0.05:
                    break
                if descriptor[i].queryIdx not in similar_descriptor_counts:
                    similar_descriptor_counts[descriptor[i].queryIdx] = 0
                similar_descriptor_counts[descriptor[i].queryIdx] += 1
        return similar_descriptor_counts

    def create_training_keypoint_set(self):
        sift_detector = cv2.SIFT.create()
        flann_matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        self.descriptors = []
        self.keypoints = []
        for slide in self.presentation.slides:
            kp, desc = (sift_detector.detectAndCompute(np.array(slide.image), None))
            self.descriptors.append(desc)
            self.keypoints += kp
            self.last_slide_kp_idx.append(len(self.keypoints) + len(kp))

        np.set_printoptions(threshold=sys.maxsize)
        self.descriptors = np.vstack(self.descriptors)
        # calculate td-idf
        last_index = 0
        descriptor_count = self.descriptors.shape[0]
        self.weights = np.ones(descriptor_count)
        mask = np.ones(descriptor_count)
        for idx in self.last_slide_kp_idx:
            slide_descriptors = self.descriptors[last_index:idx]
            # curr_slide_mask = mask
            # curr_slide_mask[last_index:idx] = 0
            same_slide_same_descriptors = flann_matcher.knnMatch(slide_descriptors, slide_descriptors,
                                                                 min(10, len(slide_descriptors)), None, False)
            same_slide_same_counts = self.count_same_descriptors(same_slide_same_descriptors)
            similar_descriptors = flann_matcher.knnMatch(slide_descriptors, self.descriptors, min(30, descriptor_count),
                                                         False, False)
            similar_descriptors_count = self.count_same_descriptors(similar_descriptors)
            for i in range(0, len(slide_descriptors)):
                same_in_frame = 1 + (same_slide_same_counts[i] if i in same_slide_same_counts else 0)
                n_in_frame = len(slide_descriptors)
                desc_db_index = last_index + i
                n_in_db = 1 + (similar_descriptors_count[desc_db_index] if desc_db_index in similar_descriptors else 0)
                slide_count = len(self.presentation.slides)
                # td-idf weight from https://www.cs.toronto.edu/~fidler/slides/2022Winter/CSC420/lecture14.pdf#page=42
                self.weights[last_index + i] = (same_in_frame / n_in_frame) * np.log10(slide_count / n_in_db)
            last_index = idx
