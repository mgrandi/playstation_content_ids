
import lzma
import pathlib

import argparse
import sys
import logging

logging.basicConfig(level="INFO")

logger = logging.getLogger("main")


def isDirectoryType(filePath):
    ''' see if the file path given to us by argparse is a directory
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a directory, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=True).expanduser()

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    # double check to see if its a file
    if not path_resolved.is_dir():
        raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

    return path_resolved

def main(args):

    dest_path = args.dest_folder
    source_path = args.source_files_folder
    path_list = source_path.glob("*.txt")

    for iter_path in path_list:

        with open(iter_path, "rb") as f:


            xz_filename = iter_path.with_suffix(".txt.xz").name
            lzma_filepath = dest_path / xz_filename

            logger.info("compressing `%s` to `%s`", iter_path, lzma_filepath)
            with lzma.open(lzma_filepath, "wb") as f2:

                f2.write(f.read())



if __name__ == "__main__":


    parser = argparse.ArgumentParser("lzma_files")

    parser.add_argument("source_files_folder", type=isDirectoryType, help="where the .txt files are located")
    parser.add_argument("dest_folder", type=isDirectoryType, help="where to put the compressed files")

    args = parser.parse_args()

    try:
        main(args)
    except Exception as e:
        logger.exception("something went wrong!")
        sys.exit(1)

    logger.info("done!")

