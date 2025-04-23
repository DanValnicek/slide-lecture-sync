import sys
from bisect import bisect
from collections import defaultdict
from math import sqrt
from typing import Sequence
import cv2
import numpy as np
from numpy import ndarray
from shapely.geometry import Polygon, box
from src import Presentation


class SlideMatcher:
    video: cv2.VideoCapture
    presentation: Presentation
    # list of keypoint/descriptor indexes of the last
    last_slide_kp_idx: list
    descriptors: list
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, presentation: Presentation):
        self.dataset_tf_idf = []
        self.slide_tf_idf_norms = []
        self.dataset_idf = []
        self.matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5})
        self.sift_detector = cv2.SIFT.create()
        self.flannIndex = None
        self.presentation = presentation
        self.last_slide_kp_idx = []
        self.keypoints = []
        self.descriptors = []

    def warp_and_recompute_slide_descriptors(self, frame, homog, slide_idx, dbg_src_pts=None):
        warped_img = cv2.warpPerspective(frame, homog, self.presentation.get_slide(slide_idx).image.size)
        kp2, desc2 = self.sift_detector.compute(warped_img, self.slideKeypoints(slide_idx), None)
        slide_descriptors = self.slideDescriptors(slide_idx)
        matches = self.matcher.knnMatch(desc2, slide_descriptors, k=1)
        if len(matches) < 5:
            return
        dataset_keypoints = self.slideKeypoints(slide_idx)
        src_pts2 = np.float32([dataset_keypoints[m[0].trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts2 = np.float32([kp2[m[0].queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        homog2, mask2 = cv2.findHomography(dst_pts2, src_pts2, cv2.USAC_ACCURATE, 1.0)
        descriptors = [self.slideIdxToDescRange(slide_idx)[0] + matches[i][0].trainIdx for i, inlier in enumerate(mask2)
                       if inlier]
        descriptors = list(dict.fromkeys(descriptors))
        if dbg_src_pts is not None:
            dbg_src_pts[:] = [(src_pts2[i], dst_pts2[i]) for i, inlier in enumerate(mask2) if inlier]
        return descriptors

    def pick_best_slide(self, matched_descriptors_from_all, slide_idxs):
        if slide_idxs == []:
            return {}
        if len(slide_idxs) == 1:
            return {slide_idxs[0]: 1}
        unique_descriptors = np.unique(np.vstack([self.descriptors[d] for d in matched_descriptors_from_all]), axis=0)
        hist = {}
        for slide_id in slide_idxs:
            matches = self.matcher.knnMatch(unique_descriptors, self.slideDescriptors(slide_id), k=1)
            distance = sum([1 if m[0].distance < 0.5 else 0 for m in matches])
            score = distance / (sqrt(len(unique_descriptors)) * sqrt(self.slideDescCnt(slide_id)))
            if score < 0.4:
                continue
            hist[slide_id] = score
        return hist

    def find_all_similar_descriptors_indexes(self, desc_index):
        maxResults = 10
        similar_matches = self.flannIndex.radiusSearch(self.descriptors[desc_index].reshape(1, -1), radius=1,
                                                       maxResults=maxResults)
        if similar_matches[0] < 1:
            return np.array([desc_index])
        similar_matches = self.flannIndex.radiusSearch(self.descriptors[desc_index].reshape(1, -1), radius=1,
                                                       maxResults=similar_matches[0])
        if desc_index not in similar_matches[1][0]:
            return np.append(similar_matches[1][0], desc_index)
        return similar_matches[1][0]

    def detect_and_sort_descriptors_from_frame(self, frame, mask):
        kp, desc = self.sift_detector.detectAndCompute(frame, mask)
        instance_cnt = defaultdict(list)
        if desc is None:
            return instance_cnt
        matches = self.flannIndex.knnSearch(desc, 2)
        for i, m in enumerate(zip(matches[0], matches[1])):
            desc_indices = m[0]
            desc_distance = m[1]
            if desc_distance[0] > desc_distance[1] - 0.5:
                similar_matches = self.find_all_similar_descriptors_indexes(desc_indices[0])
                for descriptor_idx in similar_matches:
                    index = self.descIdxToSlideIdx(descriptor_idx)
                    instance_cnt[index].append((self.keypoints[descriptor_idx].pt, kp[i].pt))
                continue
            if desc_distance[0] < desc_distance[1] * 0.9:
                descriptor_idx = desc_indices[0]
                index = self.descIdxToSlideIdx(descriptor_idx)
                instance_cnt[index].append((self.keypoints[descriptor_idx].pt, kp[i].pt))
        return instance_cnt

    @staticmethod
    def reasonableHomography(homography, src_w, src_h, dst_w, dst_h) -> bool:
        src_size = src_w * src_h
        dst_size = dst_w * dst_h
        min_scale_factor = dst_size / src_size
        max_scale_factor = dst_size / (32 * 32)
        sub_mat = np.linalg.det(homography[:2, :2])
        if not min_scale_factor * 0.9 < sub_mat <= 1.1 * max_scale_factor:
            return False
        transformed_pts = cv2.perspectiveTransform(
            np.float32([[0, 0], [0, src_h - 1], [src_w - 1, src_h - 1], [src_w - 1, 0]]).reshape(-1, 1, 2),
            homography)
        transformed_pts = [(int(x[0][0]), int(x[0][1])) for x in transformed_pts]
        transformed_polygon = Polygon(transformed_pts)
        shrinking_k = 0.78
        untouchable_rect = box(
            dst_w * (1 - shrinking_k),
            dst_h * (1 - shrinking_k),
            dst_w * shrinking_k,
            dst_h * shrinking_k
        )
        if not untouchable_rect.within(transformed_polygon):
            return False
        return True

    @staticmethod
    def spatial_pruning_and_verification(src_dst_kps, frame_h_w, slide_h_w):
        src_pts = np.float32([v[0] for v in src_dst_kps]).reshape(-1, 1, 2)
        dst_pts = np.float32([v[1] for v in src_dst_kps]).reshape(-1, 1, 2)
        homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.USAC_ACCURATE, 1.0)
        f_h, f_w, = frame_h_w
        s_h, s_w, = slide_h_w
        if homog is None or not SlideMatcher.reasonableHomography(homog, f_w, f_h, s_w, s_h):
            return
        return homog

    def matched_slide(self, frame, debug_info: list = None):
        slides_keypoints = self.detect_and_sort_descriptors_from_frame(frame, None)
        picked_descriptors = []
        picked_slides = []
        homographies = dict()
        for slide_idx, src_dst_kps in slides_keypoints.items():
            if len(src_dst_kps) < 5:
                continue
            homog = self.spatial_pruning_and_verification(
                src_dst_kps, frame.shape[:2],
                self.presentation.get_slide(slide_idx).image.size
            )
            if homog is None:
                continue
            dbg_src_pts = []
            calc_result = self.warp_and_recompute_slide_descriptors(frame, homog, slide_idx, dbg_src_pts=dbg_src_pts)
            if len(calc_result) < 10 or calc_result is None:
                continue

            homographies[slide_idx] = homog
            picked_descriptors += calc_result
            picked_slides.append(slide_idx)
            warped_img = cv2.warpPerspective(frame, homog, self.presentation.get_slide(slide_idx).image.size)
            if debug_info is not None and (debug_info is [] or len(debug_info) <= 3):
                if len(debug_info) == 3:
                    debug_info.pop(-1)
                best_keypoints1 = [cv2.KeyPoint(*x[0][0], 1) for x in dbg_src_pts]
                best_keypoints2 = [cv2.KeyPoint(*x[1][0], 1) for x in dbg_src_pts]
                debug_info.append({
                    'matched_slide': slide_idx,
                    'visual': cv2.drawMatches(
                        # frame,
                        warped_img,
                        # [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints1],
                        best_keypoints2,
                        np.array(self.presentation.get_slide(slide_idx).image)[:, :, ::-1],
                        # [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints2],
                        best_keypoints1,
                        [cv2.DMatch(i, i, 0) for i in range(len(best_keypoints1))],
                        None,
                        matchColor=(0, 255, 0),
                        singlePointColor=(255,0,0),
                        flags=cv2.DrawMatchesFlags_DEFAULT),
                    'homog': homog,
                    'warped_image': warped_img})
                # debug_info = sorted(debug_info,
                #                     key=lambda img_tup: match_histogram[img_tup['matched_slide']],
                #                     reverse=True)
        match_histogram = self.pick_best_slide(picked_descriptors, picked_slides)
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
        self.descriptors: ndarray = []
        self.keypoints = []
        for slide in self.presentation.get_all_slides():
            kp, desc = (self.sift_detector.detectAndCompute(np.array(slide.image), None))
            self.keypoints += kp
            self.last_slide_kp_idx.append(len(self.keypoints))
            if desc is None:
                continue
            self.descriptors.append(desc)
        np.set_printoptions(threshold=sys.maxsize)
        self.descriptors = np.vstack(self.descriptors)
        self.flannIndex = cv2.flann.Index(self.descriptors, {"algorithm": 1, "trees": 1})
        # calculate tf-idf
        # descriptor_count = self.descriptors.shape[0]
        # self.dataset_tf_idf = np.zeros(descriptor_count)
        # slide_count = self.presentation.get_slide_cnt()
        # for idx in range(0, slide_count):
        #     n_in_frame = self.slideDescCnt(idx)
        #     for i in range(*self.slideIdxToDescRange(idx)):
        #         same_descriptors = self.find_all_similar_descriptors_indexes(i)
        #         same_in_frame = sum(1 for x in same_descriptors if self.descIdxToSlideIdx(x) == idx)
        #         df = len({self.descIdxToSlideIdx(x) for x in same_descriptors})
        #         # td-idf weight from https://www.cs.toronto.edu/~fidler/slides/2022Winter/CSC420/lecture14.pdf#page=42
        #         self.dataset_idf.append(np.log2(slide_count / df))
        #         self.dataset_tf_idf[i] = (same_in_frame / n_in_frame) * self.dataset_idf[i]
        #     self.slide_tf_idf_norms.append(np.linalg.norm(self.dataset_tf_idf[slice(*self.slideIdxToDescRange(idx))]))
