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
    descriptors: np.ndarray
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, presentation: Presentation):
        self.keypoint_clusters = None
        self.presentation = presentation
        self.last_slide_kp_idx = []
        self.keypoints = []
        self.descriptors = []
        self.dataset_tf_idf = []
        self.dataset_idf = []
        self.slide_tf_idf_norms = []

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

    def matched_slide(self, frame, debug_info: list = None) -> (int, int):
        # debug_info = []
        matcher = cv2.SIFT.create()

        kp, desc = matcher.detectAndCompute(frame, None)
        bfm = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        matches = bfm.knnMatch(desc, self.descriptors, k=1)
        instance_cnt = defaultdict(list)

        for m in matches:
            index = bisect(self.last_slide_kp_idx, m[0].trainIdx)
            instance_cnt[index].append(m[0])
        match_histogram = dict()
        for slide_idx, slide_matches in sorted(instance_cnt.items(), key=lambda x: len(x[1]), reverse=True):
            # kps_lower_idx = self.last_slide_kp_idx[slide_idx - 1] if slide_idx != 0 else 0
            # kps_upper_idx = self.last_slide_kp_idx[slide_idx]
            if len(slide_matches) < 5:
                del instance_cnt[slide_idx]
                continue

            db_tf_idf = [self.dataset_tf_idf[m.trainIdx] for m in slide_matches]
            db_idf = [self.dataset_idf[m.trainIdx] for m in slide_matches]
            src_pts = np.float32([self.keypoints[m.trainIdx].pt for m in slide_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp[m.queryIdx].pt for m in slide_matches]).reshape(-1, 1, 2)

            homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
            f_w, f_h = frame.shape[:2]
            s_w, s_h = self.presentation.slides[slide_idx].image.size
            if homog is None or not HomographyProcessor.reasonableHomography(homog, f_w, f_h, s_w, s_h):
                continue

            transformed_pts = cv2.perspectiveTransform(dst_pts, homog)
            eval_sum = 0.0
            significant_kp = []
            train_slide_offset = (self.last_slide_kp_idx[slide_idx - 1] if slide_idx > 0 else 0)
            slide_len = self.last_slide_kp_idx[slide_idx] - train_slide_offset
            q_tf_idf_vec = []
            valid_cnt = 0
            for i in range(len(transformed_pts)):
                # eval_sum += self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i])
                if (
                        match_score := self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i]) * db_tf_idf[
                            i]) > 0.0:
                    significant_kp.append(slide_matches[i])
                    q_tf_idf_vec.append(db_idf[i])
                    valid_cnt += 1
                    # eval_sum += match_score
                else:
                    q_tf_idf_vec.append(0.0)
            if valid_cnt < 4:
                del instance_cnt[slide_idx]
                continue
            # match_histogram[slide_idx] = eval_sum
            q_tf_idf_vec = [x / valid_cnt for x in q_tf_idf_vec]

            # warped_img = cv2.warpPerspective(frame, homog, self.presentation.slides[slide_idx].image.size)
            # kp2, desc2 = matcher.detectAndCompute(warped_img, None)
            # matches = bfm.knnMatch(desc2, self.descriptors[train_slide_offset: self.last_slide_kp_idx[slide_idx]], k=1)
            # db_tf_idf = [self.dataset_tf_idf[m.trainIdx] for m in matches]
            # db_idf = [self.dataset_idf[m.trainIdx] for m in matches]
            # src_pts = np.float32([self.keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
            # dst_pts = np.float32([kp[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            # slide_len = self.last_slide_kp_idx[slide_idx] - train_slide_offset
            # match_histogram[slide_idx] = eval_sum
            # q_tf_idf_vec = [x / valid_cnt for x in q_tf_idf_vec]
            match_histogram[slide_idx] = np.dot(q_tf_idf_vec, db_tf_idf) / (
                    np.linalg.norm(q_tf_idf_vec) * self.slide_tf_idf_norms[
                slide_idx]) * (valid_cnt/slide_len)

            if (debug_info is not None
                    and (
                            debug_info is []
                            or len(debug_info) <= 3
                            or match_histogram.get(debug_info[-1]['matched_slide'], 0) < eval_sum
                    )
            ):
                if len(debug_info) == 3:
                    debug_info.pop(-1)
                best_keypoints1 = [kp[m.queryIdx].pt for m in significant_kp]
                best_keypoints2 = [self.keypoints[m.trainIdx].pt for m in significant_kp]
                debug_info.append({
                    'matched_slide': slide_idx,
                    'visual': cv2.drawMatches(
                        frame,
                        [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints1],
                        np.array(self.presentation.slides[slide_idx].image)[:, :, ::-1],
                        [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints2],
                        [cv2.DMatch(i, i, 0) for i in range(len(best_keypoints1))],
                        None,
                        flags=cv2.DrawMatchesFlags_DEFAULT),
                    'homog': homog,
                    'warped_image': cv2.warpPerspective(frame, homog, self.presentation.slides[
                        slide_idx].image.size)})
                debug_info = sorted(debug_info,
                                    key=lambda img_tup: match_histogram[img_tup['matched_slide']],
                                    reverse=True)
        if match_histogram == {}:
            return match_histogram, None, None
        return match_histogram, max(match_histogram, key=match_histogram.get), debug_info

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
        sift_detector = cv2.SIFT.create()
        flann_matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        self.descriptors = []
        self.keypoints = []
        for slide in self.presentation.slides:
            kp, desc = (sift_detector.detectAndCompute(np.array(slide.image), None))
            self.descriptors.append(desc)
            self.keypoints += kp
            self.last_slide_kp_idx.append(len(self.keypoints))

        np.set_printoptions(threshold=sys.maxsize)
        self.descriptors = np.vstack(self.descriptors)
        # calculate tf-idf
        last_index = 0
        descriptor_count = self.descriptors.shape[0]
        self.dataset_tf_idf = np.ones(descriptor_count)
        slide_count = len(self.presentation.slides)
        for idx in self.last_slide_kp_idx:
            slide_descriptors = self.descriptors[last_index:idx]
            same_slide_same_descriptors = flann_matcher.knnMatch(slide_descriptors, slide_descriptors,
                                                                 min(10, len(slide_descriptors)), None, False)
            same_slide_same_counts = self.count_same_descriptors(same_slide_same_descriptors)
            similar_descriptors = flann_matcher.knnMatch(slide_descriptors, self.descriptors,
                                                         min(30, descriptor_count),
                                                         False, False)
            df = self.count_documents_containing_term(similar_descriptors)

            # similar_descriptors_count = self.count_same_descriptors(similar_descriptors)
            n_in_frame = len(slide_descriptors)
            for i in range(0, len(slide_descriptors)):
                same_in_frame = same_slide_same_counts.get(i, 0)
                # td-idf weight from https://www.cs.toronto.edu/~fidler/slides/2022Winter/CSC420/lecture14.pdf#page=42
                self.dataset_idf.append(np.log2((slide_count) / (df[i])))
                self.dataset_tf_idf[last_index + i] = (same_in_frame / n_in_frame) * self.dataset_idf[last_index + i]
            self.slide_tf_idf_norms.append(np.linalg.norm(self.dataset_tf_idf[last_index:idx]))
            last_index = idx
