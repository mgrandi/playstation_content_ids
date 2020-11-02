import argparse
import subprocess
import logging
import sys
import pathlib
import shlex
import tempfile
import os
import hashlib
import lzma
import shutil

logger = None
def main(args):

    if not shutil.which("dos2unix"):
        logger.error("You need the `dos2unix` program to run this! run `sudo apt install dos2unix` maybe?")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as temp_dir_name:

        logger.debug("temp directory is `%s`", temp_dir_name)

        # will include any temporary extracted files from `xzcat`
        cat_cmd_list = ["/usr/bin/cat"]

        xz_cat_cmd_list = ["/usr/bin/xzcat"]

        logger.info("combining files...")
        logger.info(" ")

        for iter_path in args.files:


            # if its an XZ file, we add it to a different list so we can extract it first
            if iter_path.suffix == ".xz":

                xz_cat_cmd_list.append(str(iter_path))


                # get the hash of the xz file as well as internal contents
                with open(iter_path, "rb") as f:

                    # hash total xz file
                    hasher = hashlib.sha256()
                    hasher.update(f.read())
                    logger.info("sha256 of `%s` is `%s`", iter_path, hasher.hexdigest())

                # hash contents of xz file
                with lzma.open(iter_path, "rb") as f:
                    # hash file
                    hasher = hashlib.sha256()
                    hasher.update(f.read())
                    logger.info("sha256 of files within `%s` is `%s`", iter_path, hasher.hexdigest())

                # get line count
                cmd_one_list = ["/usr/bin/xzcat", str(iter_path)]
                cmd_two_list = ["/usr/bin/wc", "-l"]
                final_cmd = f"{shlex.join(cmd_one_list)} | {shlex.join(cmd_two_list)}"
                logger.debug("running wc command: `%s`", final_cmd)
                x = subprocess.run(final_cmd, stdout=subprocess.PIPE, shell=True)
                logger.info("line # of files within `%s` is `%s`", iter_path, x.stdout)

            else:

                # not an xz file, add to normal list of files to combine using regular cat

                # convert from pathlib.Path
                cat_cmd_list.append(str(iter_path))

                with open(iter_path, "rb") as f:

                    # hash file
                    hasher = hashlib.sha256()
                    hasher.update(f.read())
                    logger.info("sha256 of `%s` is `%s`", iter_path, hasher.hexdigest())

                    # get line count
                    cmd_list = ["/usr/bin/wc", "-l", iter_path]
                    logger.debug("running wc command: `%s`", cmd_list)
                    x = subprocess.run(cmd_list, stdout=subprocess.PIPE)
                    logger.info("line # of `%s` is `%s`", iter_path, x.stdout)


            logger.info(" ")


        sort_cmd_list = ["/usr/bin/sort"]
        uniq_cmd_list = ["/usr/bin/uniq"]
        dos2unix_cmd_list = ["/usr/bin/dos2unix"]

        xzcat_output_path = pathlib.Path(temp_dir_name) / "tmp.txt"
        no_dos2unix_file_path = pathlib.Path(temp_dir_name) / "no_dos2unix.txt"

        logger.info("calling `sort | uniq` ...")
        logger.info(" ")

        # only run this if we have any xz files
        # run `xzcat` on all of our xz files to concat them into one combined file that
        # we can then also pass to regular `cat`
        if len(xz_cat_cmd_list) > 1:
            logger.debug("have xz files, writing xzcat output to `%s`", xzcat_output_path)

            # run xz extracts to temp directory
            with open(xzcat_output_path, "wb") as f:
                os.set_inheritable(f.fileno(), True)

                logger.debug("running xzcat cmd: `%s`", xz_cat_cmd_list)
                xzcat_res = subprocess.run(xz_cat_cmd_list, stdout=f)

                logger.debug("xzcat process result: `%s`", xzcat_res)

                wc_cmd_list = ["/usr/bin/wc", "-l", xzcat_output_path]
                wc_res = subprocess.run(wc_cmd_list, stdout=subprocess.PIPE)
                logger.debug("line # of xzcat output: `%s`", wc_res.stdout)

            # now add the xzcat output to the cat cmd list to include it with everything else
            cat_cmd_list.append(str(xzcat_output_path))


        # now run the final cat / sort / unique commands

        final_cmd_no_dos2unix = f"{shlex.join(cat_cmd_list)} | {shlex.join(sort_cmd_list)} | {shlex.join(uniq_cmd_list)}"
        final_cmd = f"{shlex.join(cat_cmd_list)} | {shlex.join(dos2unix_cmd_list)} | {shlex.join(sort_cmd_list)} | {shlex.join(uniq_cmd_list)}"

        # do a test without dos2unix for comparison purposes for old files that didn't run that
        with open(no_dos2unix_file_path, "wb") as f:

            logger.debug("running cat/sort/uniq without dos2unix: `%s`", final_cmd_no_dos2unix)

            nod2u_res = subprocess.run(final_cmd_no_dos2unix, stdout=f, shell=True)

            logger.debug("final process with no dos2unix result: `%s`", nod2u_res)

        with open(no_dos2unix_file_path, "rb") as f:

            # hash file
            hasher = hashlib.sha256()
            hasher.update(f.read())
            logger.info("sha256 of final file (no dos2unix) `%s` is `%s`", no_dos2unix_file_path, hasher.hexdigest())

            # get line count
            cmd = ["/usr/bin/wc", "-l", no_dos2unix_file_path]
            logger.debug("running wc command: `%s`", cmd)
            x = subprocess.run(cmd, stdout=subprocess.PIPE)
            logger.info("line # of final file (no dos2unix) `%s` is `%s`", no_dos2unix_file_path, x.stdout)


        # run actual final command with dos2unix and everything else
        with open(args.output, "wb") as f:

            logger.debug("running cat/sort/uniq cmd with dos2unix: `%s`", final_cmd)

            final_cmd_res = subprocess.run(final_cmd, stdout=f, shell=True)

            logger.debug("final process result: `%s`", final_cmd_res)

            logger.info("wrote final file to `%s`", args.output)

        with open(args.output, "rb") as f:

            # hash file
            hasher = hashlib.sha256()
            hasher.update(f.read())
            logger.info("sha256 of final file `%s` is `%s`", args.output, hasher.hexdigest())

            # get line count
            cmd = ["/usr/bin/wc", "-l", args.output]
            logger.debug("running wc command: `%s`", cmd)
            x = subprocess.run(cmd, stdout=subprocess.PIPE)
            logger.info("line # of final file `%s` is `%s`", args.output, x.stdout)

        logger.info("done")


def isFileType(strict=True):
    def _isFileType(filePath):
        ''' see if the file path given to us by argparse is a file
        @param filePath - the filepath we get from argparse
        @return the filepath as a pathlib.Path() if it is a file, else we raise a ArgumentTypeError'''

        path_maybe = pathlib.Path(filePath)
        path_resolved = None

        # try and resolve the path
        try:
            path_resolved = path_maybe.resolve(strict=strict).expanduser()

        except Exception as e:
            raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

        # double check to see if its a file
        if path_resolved.is_dir():
            raise argparse.ArgumentTypeError("the path `{}` is a directory!".format(path_resolved))
        if strict:
            if not path_resolved.is_file():
                raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

        return path_resolved
    return _isFileType


parser = argparse.ArgumentParser(description="helper for merging a mixture of text files and xz compressed text files")
parser.add_argument("--verbose", action="store_true", help="increase logger verbosity")

# it is a long argument because you might need to specify it after the files and this is the only way to do it without it trying to parse
# this argument as part of the 'files'
parser.add_argument("--output", type=isFileType(False), required=True, help="the path to save the merged file (full filepath)")
parser.add_argument("files", nargs="+", type=isFileType(True), help="the files to merge")


parsed_args = parser.parse_args()

fmt = "%(levelname)s - %(message)s"
if parsed_args.verbose:
    logging.basicConfig(level="DEBUG", format=fmt)
else:
    logging.basicConfig(level="INFO", format=fmt)

logger = logging.getLogger()

logger.debug("parsed arguments: `%s`", parsed_args)


try:
    main(parsed_args)
except Exception as e:
    logger.exception("something went wrong!")
    sys.exit(1)
