# timestamps in microseconds
slides_with_timestamps = [
    {'time': 1630356020, 'label': 1}, {'time': 1734066007, 'label': 2},
    {'time': 1738316007, 'label': 3}, {'time': 1825606003, 'label': 4},
    {'time': 1827486000, 'label': 5}, {'time': 1906565991, 'label': 6},
    {'time': 1951735985, 'label': 7}, {'time': 1983984982, 'label': 8},
    {'time': 2003735976, 'label': 9}, {'time': 2098066968, 'label': 10},
    {'time': 2105566968, 'label': 11}, {'time': 2187735959, 'label': 12},
    {'time': 2232566954, 'label': 13}, {'time': 2306065947, 'label': 14},
    {'time': 2408105936, 'label': 15}, {'time': 2453064931, 'label': 16},
    {'time': 2501105924, 'label': 17}, {'time': 2575236918, 'label': 18},
    {'time': 2646236909, 'label': 19}, {'time': 2695315902, 'label': 20},
    {'time': 2757316894, 'label': 21}, {'time': 2758235893, 'label': 22},
    {'time': 2759235893, 'label': 23}, {'time': 2760986893, 'label': 24},
    {'time': 2960565874, 'label': 25}, {'time': 3134105854, 'label': 26},
    {'time': 3134855854, 'label': 27}, {'time': 3135604854, 'label': 28},
    {'time': 3268814842, 'label': 29}, {'time': 3307065838, 'label': 30},
    {'time': 3312565838, 'label': 31}, {'time': 3313606837, 'label': 32},
    {'time': 3318355837, 'label': 33}, {'time': 3320356837, 'label': 34},
    {'time': 3321105837, 'label': 35}, {'time': 3321355837, 'label': 36},
    {'time': 3538605832, 'label': 37}, {'time': 3540355831, 'label': 38},
    {'time': 3541105831, 'label': 39}, {'time': 3541855831, 'label': 40},
    {'time': 3543105831, 'label': 42}, {'time': 3545855831, 'label': 42},
    {'time': 3881355809, 'label': 43}, {'time': 3881859809, 'label': 44},
    {'time': 3882355809, 'label': 45}, {'time': 3948606802, 'label': 45},
    {'time': 3960316797, 'label': 46}, {'time': 3960564800, 'label': 47},
    {'time': 4013355793, 'label': 48}, {'time': 4030106791, 'label': 50},
    {'time': 4053354791, 'label': 51}, {'time': 4107816786, 'label': 52},
    {'time': 4118065786, 'label': 53}, {'time': 4118314786, 'label': 54},
    {'time': 4118815786, 'label': 55}, {'time': 4119815786, 'label': 56},
    {'time': 4223565776, 'label': 56}, {'time': 4236315776, 'label': 57},
    {'time': 4237065776, 'label': 59}, {'time': 4237815776, 'label': 60},
    {'time': 4353315764, 'label': 61}, {'time': 4354815764, 'label': 61},
    {'time': 4408314758, 'label': 63}, {'time': 4445855756, 'label': 64},
    {'time': 4446605756, 'label': 65}, {'time': 4465605756, 'label': 66},
    {'time': 4474856755, 'label': 67}, {'time': 4475105755, 'label': 67},
    {'time': 4475855755, 'label': 69}, {'time': 4476355755, 'label': 70},
    {'time': 4477606755, 'label': 71}, {'time': 4479855755, 'label': 72},
    {'time': 4515814982, 'label': 73}, {'time': 4516316982, 'label': 74},
    {'time': 4738818962, 'label': 74}, {'time': 4740066962, 'label': 76},
    {'time': 4741065962, 'label': 77}, {'time': 4742064962, 'label': 78},
    {'time': 4743065962, 'label': 79}, {'time': 4910066948, 'label': 80},
    {'time': 4912815947, 'label': 81}, {'time': 4913564947, 'label': 82},
    {'time': 4914315947, 'label': 83}, {'time': 4992734942, 'label': 84},
    {'time': 4993234942, 'label': 85}, {'time': 4993735942, 'label': 86}]


# class IDM_testing:
#     video_path = os.path.join(pathlib.Path(__file__).parent.parent.resolve(), "data/videos/IDM_2023-11-07_1080p.mp4")
#     # video_path = "/home/valnicek/pycharmProjects/BP_Homography/data/videos/IDM_2023-11-07_1080p.mp4"
#     presentation_path = pathlib.Path(os.path.join(pathlib.Path(__file__).parent.resolve(), "data/grafy1.pdf"))
#
#     def get_slide_with_timestamp(self) -> (int, float):
#         for val in slides_with_timestamps:
#             # subtract 1 to align with 0 based counting
#             yield val['label'] - 1, val['time'] / 1000
