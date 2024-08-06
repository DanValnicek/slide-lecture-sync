import time

from pdf2image import convert_from_path

fmts = ["jpg", "png", "tif", "ppm"]
for grayscale in [False, True]:
    for fmt in fmts:
        t0 = time.time()
        path = "./tmp/"
        images_from_path = convert_from_path(
            "./data/pdfs/IPK2023-24L-07-MULTICAST.pdf",
            grayscale=grayscale, fmt=fmt, size=(480, None),
            output_folder=path)
        t1 = time.time()
        print(fmt, " gray: ", grayscale, " speed: ", t1 - t0)
