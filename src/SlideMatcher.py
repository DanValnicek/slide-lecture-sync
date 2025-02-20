import sys
from bisect import bisect
from collections import defaultdict
from functools import cmp_to_key
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
    descriptors: np.ndarray
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, presentation: Presentation):
        self.matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        self.sift_detector = cv2.SIFT.create()
        self.flannIndex = None
        self.keypoint_clusters = None
        self.presentation = presentation
        self.last_slide_kp_idx = []
        self.keypoints = []
        self.descriptors = []
        self.dataset_tf_idf = []
        self.dataset_idf = []
        self.slide_tf_idf_norms = []
        self.slide_zone_cnt = []

    # def matchPresentationToVideo(self):
    @staticmethod
    def eval_keypoints_by_distance(src_keypoint1: cv2.KeyPoint, dst_keypoint2: cv2.KeyPoint) -> float:
        """https://www.desmos.com/calculator/9ag3brj92d"""
        distance = np.linalg.norm(src_keypoint1 - dst_keypoint2)
        # if distance > 7.0:
        if distance > 14.0:
            return 0.0
        return 1.0
        # return np.exp(-(distance ** 2) / (2 * 3 ** 2))
        return np.exp(-(distance ** 2) / (2 * 6 ** 2))

    def calc_coverage(self, frame, homog, slide_idx):
        warped_img = cv2.warpPerspective(frame, homog, self.presentation.slides[slide_idx].image.size)
        kp2, desc2 = self.sift_detector.compute(warped_img, self.keypoints[slice(*self.slideIdxToDescRange(slide_idx))],
                                                None)
        matches = self.matcher.knnMatch(desc2, self.descriptors[slice(*self.slideIdxToDescRange(slide_idx))], k=1)
        if len(matches) < 5:
            return
        range_s, range_e = self.slideIdxToDescRange(slide_idx)
        dataset_keypoints = self.keypoints[range_s:range_e]
        src_pts2 = np.float32([dataset_keypoints[m[0].trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts2 = np.float32([kp2[m[0].queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        homog2, mask2 = cv2.findHomography(dst_pts2, src_pts2, cv2.RANSAC, 7.0)
        src_kps2 = []
        for i, v in enumerate(src_pts2):
            if mask2[i]:
                src_kps2.append(cv2.KeyPoint(v[0][0], v[0][1], 1))
        s_h, s_w, = self.presentation.slides[slide_idx].image.size
        return self.patch_coverage2(src_kps2, s_w, s_h)

    def matched_slide(self, frame, debug_info: list = None, previous_homography=None, previous_slide_idx=None,
                      previous_coverage=None):
        # debug_info = []
        # if previous_homography is not None and previous_slide_idx is not None and previous_coverage is not None:
        #     if self.calc_coverage(frame, previous_homography, previous_slide_idx) == previous_coverage:
        #         return pre
        frame_copy = None
        if previous_homography is not None:
            frame_copy = frame.copy()
            frame = cv2.warpPerspective(
                frame, previous_homography, self.presentation.slides[previous_slide_idx].image.size
            )
        kp, desc = self.sift_detector.detectAndCompute(frame, None)
        matches = self.flannIndex.knnSearch(desc, 1)
        instance_cnt = defaultdict(list)

        for i, m in enumerate(matches[0]):
            index = self.descIdxToSlideIdx(m[0])
            instance_cnt[index].append((self.keypoints[m[0]].pt, kp[i].pt))
        match_histogram = dict()
        patch_results = {}
        for slide_idx, src_dst_kps in instance_cnt.items():
            if len(src_dst_kps) < 5:
                continue
            src_pts = np.float32([v[0] for v in src_dst_kps]).reshape(-1, 1, 2)
            dst_pts = np.float32([v[1] for v in src_dst_kps]).reshape(-1, 1, 2)
            homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 1.0)
            f_h, f_w, = frame.shape[:2]
            s_h, s_w, = self.presentation.slides[slide_idx].image.size
            if homog is None or not HomographyProcessor.reasonableHomography(homog, f_w, f_h, s_w, s_h):
                continue
                # patch_results[slide_idx] = self.calc_coverage(frame, homog, slide_idx)
            frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            slide_grey = cv2.cvtColor(np.array(self.presentation.slides[slide_idx].image), cv2.COLOR_BGR2GRAY)
            corr_image = cv2.matchTemplate(frame_grey, slide_grey, cv2.TM_CCORR_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(corr_image)
            match_histogram[slide_idx] = max_val
            # match_histogram[slide_idx] = (patch_cnt + (patch_cnt - self.slide_zone_cnt[slide_idx])) / \
            #                              self.slide_zone_cnt[slide_idx]
            # match_histogram[slide_idx] = patch_cnt - self.slide_zone_cnt[slide_idx]
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
                    # 'homog2': homog2,
                    'warped_image': corr_image})
                debug_info = sorted(debug_info,
                                    key=lambda img_tup: match_histogram[img_tup['matched_slide']],
                                    reverse=True)
        # slide_patches = [(self.slide_zone_cnt[slide_id], patches, slide_id) for slide_id, patches in
        #                  patch_results.items()]
        # slide_patches.sort(key=cmp_to_key(self.cmp_patches))
        # for i, slide_patches in enumerate(slide_patches):
        #     match_histogram[slide_patches[2]] = i
        if match_histogram == {} and previous_homography is not None:
            return self.matched_slide(frame_copy, debug_info)
        if match_histogram == {}:
            return match_histogram, None, None
        return match_histogram, max(match_histogram, key=match_histogram.get), debug_info

    @staticmethod
    def cmp_patches(a, b):
        unique_a = len(a[1] - b[1])
        unique_b = len(b[1] - a[1])
        if abs(unique_a - unique_b) < 5:
            return b[0] - a[0]
        return unique_a - unique_b

    @staticmethod
    def count_same_descriptors(desc_query_results):
        similar_descriptor_counts = dict()
        for descriptor in desc_query_results:
            for i in range(0, len(descriptor)):
                # if descriptor[i].queryIdx == descriptor[i].trainIdx:
                #     continue
                if descriptor[i].distance > 0.05:
                    break
                if descriptor[i].queryIdx not in similar_descriptor_counts:
                    similar_descriptor_counts[descriptor[i].queryIdx] = 0
                similar_descriptor_counts[descriptor[i].queryIdx] += 1
        return similar_descriptor_counts

    def descIdxToSlideIdx(self, train_id):
        return bisect(self.last_slide_kp_idx, train_id)

    def slideIdxToDescRange(self, slide_idx) -> tuple[int, int]:
        if slide_idx == 0:
            return 0, self.last_slide_kp_idx[0]
        return self.last_slide_kp_idx[slide_idx - 1], self.last_slide_kp_idx[slide_idx]

    def slideDescCnt(self, slide_idx):
        if slide_idx == 0:
            return self.last_slide_kp_idx[0]
        return self.last_slide_kp_idx[slide_idx] - self.last_slide_kp_idx[slide_idx - 1]

    def count_documents_containing_term(self, desc_query_results):
        slides_w_similar_desc = dict()
        for descriptor in desc_query_results:
            for i in range(0, len(descriptor)):
                if descriptor[i].distance > 0.05:
                    break
                slide_idx = self.descIdxToSlideIdx(descriptor[i].trainIdx)
                if descriptor[i].queryIdx not in slides_w_similar_desc:
                    slides_w_similar_desc[descriptor[i].queryIdx] = []
                slides_w_similar_desc[descriptor[i].queryIdx].append(slide_idx)
        df = {i: len(set(arr)) for i, arr in slides_w_similar_desc.items()}
        return df

    def create_training_keypoint_set(self):
        # flann_matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        self.descriptors = []
        self.keypoints = []
        for slide in self.presentation.slides:
            kp, desc = (self.sift_detector.detectAndCompute(np.array(slide.image), None))
            self.descriptors.append(desc)
            self.keypoints += kp
            self.slide_zone_cnt.append(
                self.patch_coverage(kp, slide.image.size[1], slide.image.size[0])
            )
            self.last_slide_kp_idx.append(len(self.keypoints))

        np.set_printoptions(threshold=sys.maxsize)
        self.descriptors = np.vstack(self.descriptors)
        self.flannIndex = cv2.flann.Index(self.descriptors, {"algorithm": 1, "trees": 5})
        # calculate tf-idf
        last_index = 0
        descriptor_count = self.descriptors.shape[0]
        self.dataset_tf_idf = np.ones(descriptor_count)
        # slide_count = len(self.presentation.slides)
        # for idx in self.last_slide_kp_idx:
        #     slide_descriptors = self.descriptors[last_index:idx]
        #     same_slide_same_descriptors = flann_matcher.knnMatch(slide_descriptors, slide_descriptors,
        #                                                          min(10, len(slide_descriptors)), None, False)
        #     same_slide_same_counts = self.count_same_descriptors(same_slide_same_descriptors)
        #     similar_descriptors = flann_matcher.knnMatch(
        #         slide_descriptors, self.descriptors,
        #         min(30, descriptor_count),
        #         False, False
        #     )
        #     df = self.count_documents_containing_term(similar_descriptors)
        #
        #     # similar_descriptors_count = self.count_same_descriptors(similar_descriptors)
        #     n_in_frame = len(slide_descriptors)
        #     for i in range(0, len(slide_descriptors)):
        #         same_in_frame = same_slide_same_counts.get(i, 0)
        #         # td-idf weight from https://www.cs.toronto.edu/~fidler/slides/2022Winter/CSC420/lecture14.pdf#page=42
        #         self.dataset_idf.append(np.log2((slide_count) / (df[i])))
        #         self.dataset_tf_idf[last_index + i] = (same_in_frame / n_in_frame) * self.dataset_idf[last_index + i]
        #     self.slide_tf_idf_norms.append(np.linalg.norm(self.dataset_tf_idf[last_index:idx]))
        #     last_index = idx

    @staticmethod
    def patch_coverage(keypoints: list[cv2.KeyPoint], width, height, mask=None):
        zone_counts = dict()
        for i, keypoint in enumerate(keypoints):
            if mask is None or mask[i]:
                zone_counts[(keypoint.pt[0] // (height // 15), keypoint.pt[1] // (width // 15))] = True
        return len(zone_counts.keys())

    @staticmethod
    def patch_coverage2(keypoints: list[cv2.KeyPoint], width, height, mask=None):
        zone_counts = set()
        for i, keypoint in enumerate(keypoints):
            if mask is None or mask[i]:
                zone_counts.add((keypoint.pt[0] // (height // 15), keypoint.pt[1] // (width // 15)))
        return zone_counts
