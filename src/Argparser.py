import logging
from argparse import ArgumentParser
from pathlib import Path


class CustomArgParser(ArgumentParser):
    description = 'Extract images from video'
    _parsed_args = None

    def __init__(self):
        super().__init__()
        self.add_argument('--video', '-v', type=str)
        self.add_argument('--pdf', type=Path)
        self.add_argument('-log', '--log', type=str, default='INFO')
        logging.basicConfig(level=self.parse_args().log)
        # logging.getLogger(__name__).debug("program args: " + self.pdf)

    def parse_args(self, args=None, namespace=None):
        args = super().parse_args(args, namespace)
        logging.getLogger(__name__).debug("program args: " + str(args.pdf))
        return args

    @classmethod
    def get_args(cls):
        if cls._parsed_args is None:
            cls._parsed_args = cls().parse_args()
        return cls._parsed_args
