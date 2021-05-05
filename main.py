import argparse
from distutils import dir_util
from distutils.errors import DistutilsFileError
import pathlib
import os
import sys
import textwrap
import zipfile
import requests
from loguru import logger

from version import __version__


PROXIES = {"http": None, "https": None}
ROOT_CA_FILENAME = None
BASE_URL = "https://storage.googleapis.com/chromium-browser-snapshots"

PLATFORM_METADATA = {
    "mac": {"PLATFORM": "Mac", "PKGNAME": "chrome-mac.zip"},
    "linux": {"PLATFORM": "Linux", "PKGNAME": "chrome-linux.zip"},
    "win": {"PLATFORM": "Win_x64", "PKGNAME": "chrome-win.zip"},
}


class DownloadParameter:
    """
    """

    def __init__(self, output_directory, platform: str):
        self.output_directory = output_directory
        self.platform = platform


class RequestsParameter:
    """
    """

    def __init__(self, url, proxies, root_ca):
        self.url = url
        self.proxies = proxies
        self.root_ca = root_ca


def create_clean_directory(directory: pathlib.Path):
    """
    """
    if directory.is_absolute() and directory.is_dir():
        dir_util.remove_tree(str(directory))
    try:
        os.mkdir(directory)
    except FileNotFoundError:
        logger.error("make sure parent directories of {} exist".format(directory))


def download(download_parameters: DownloadParameter) -> pathlib.Path:
    """
    """
    output_directory = pathlib.Path(download_parameters.output_directory).resolve()
    if not (output_directory.is_dir() and output_directory.is_absolute()):
        logger.error("{} is not an absolute directory".format(output_directory))
        sys.exit(-1)

    requests_parameters = RequestsParameter("", PROXIES, ROOT_CA_FILENAME)

    PLATFORM = PLATFORM_METADATA.get(download_parameters.platform, "win").get("PLATFORM", "Win_x64")
    PKGNAME = PLATFORM_METADATA.get(download_parameters.platform, "win").get("PKGNAME", "chrome-win.zip")

    LAST_CHANGE_URL = BASE_URL + "/" + PLATFORM + "/LAST_CHANGE"
    requests_parameters.url = LAST_CHANGE_URL

    last_change_response = requests.get(
        requests_parameters.url, proxies=requests_parameters.proxies, verify=requests_parameters.root_ca
    )

    if last_change_response.status_code != 200:
        logger.error("Fetching last change failed with status code ({})".format(last_change_response.status_code))
        sys.exit(-1)

    LAST_VERSION = last_change_response.text
    logger.info("LAST_CHANGE: {}".format(LAST_VERSION))

    DOWNLOAD_URL = BASE_URL + "/" + PLATFORM + "/" + LAST_VERSION + "/" + PKGNAME
    requests_parameters.url = DOWNLOAD_URL

    chromium_download_response = requests.get(
        requests_parameters.url, proxies=requests_parameters.proxies, verify=requests_parameters.root_ca
    )

    if chromium_download_response.status_code != 200:
        logger.error("Download failed with status code ({})".format(last_change_response.status_code))
        sys.exit(-1)

    output_file_name = PLATFORM + "_" + LAST_VERSION + "_" + PKGNAME

    output_file = pathlib.Path(output_directory.joinpath(output_file_name))
    logger.info("Writing output file to: {}".format(output_file))
    bytes_written = output_file.write_bytes(chromium_download_response.content)
    logger.info("{} bytes written".format(bytes_written))
    return output_file


def install(zip_file: pathlib.Path, install_directory: pathlib.Path, platform: str):
    """
    """
    archive_file = zipfile.ZipFile(zip_file)
    extraction_directory = pathlib.Path(zip_file.stem).resolve()
    if not zip_file.is_file():
        logger.error("Zip file {} does not exist.".format(zip_file))
        return
    create_clean_directory(extraction_directory)
    if platform == "win":
        create_clean_directory(install_directory)
        if not extraction_directory.is_dir():
            logger.error("Extraction directory {} does not exist".format(extraction_directory))
            return
        if not install_directory.is_dir():
            logger.error("Installation directory {} does not exist".format(install_directory))
            return
        logger.info("Extracting to intermediate directory {}".format(extraction_directory))
        archive_file.extractall(extraction_directory)
        PKG_BASE_NAME = PLATFORM_METADATA.get(args.platform, "win").get("PKGNAME", "chrome-win.zip").split(".")[0]

        try:
            src = str(extraction_directory.resolve().joinpath(PKG_BASE_NAME))
            dst = str(install_directory)
            logger.info("Recursively copying content of {} to {}".format(src, dst))
            dir_util.copy_tree(src, dst)
        except DistutilsFileError as e:
            logger.error("Error while copying extracted sources from {} to {}\n\t{}".format(src, dst, str(e)))
        finally:
            logger.info("Cleaning up intermediate extraction directory {}".format(extraction_directory))
            dir_util.remove_tree(extraction_directory)
    elif platform == "mac":
        if not extraction_directory.is_dir():
            logger.error("Extraction directory {} does not exist".format(extraction_directory))
            return
        logger.info("Extracting to intermediate directory {}".format(extraction_directory))
        archive_file.extractall(extraction_directory)
    elif platform == "linux":
        logger.error("Use your package manager")
        return
    else:
        logger.warning("Installation on {} not implemented".format(platform))
        return
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Fetches the latest builds of Chromium for Windows, Mac, Linux",
        epilog=textwrap.dedent(
            r"""
        Examples
        --------

        Fetch the latest archive for a Mac and store the file in the current directory
            > python main.py --platform mac --output_directory .

        Fetch the latest archive for a Mac using a proxy and store the file in the current directory
            > python main.py --platform mac --output_directory . --proxy http://proxy.example.com:80

        Fetch the latest archive for Windows using a proxy, store the file in
        the current directory, and install it to C:\chromium
            > python main.py --platform win --output_directory .  --install C:\chromium --proxy http://proxy.example.com:80 --root_ca root_ca.cer
        """
        ),
    )
    parser.add_argument(
        "-o",
        "--output_directory",
        help="Directory where the output file is written",
        type=str,
        default=".",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--platform",
        help="Platform where Chromium should run",
        type=str,
        choices=["mac", "win", "linux"],
        default="win",
        required=True,
    )
    parser.add_argument("-i", "--install", help="Where to clean and install chromium", type=str, default="")
    parser.add_argument("--proxy", help="use proxy", type=str, default=None)
    parser.add_argument("-ca", "--root_ca", help="path to a root ca of the proxy for example", type=str, default=None)
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args()

    PROXIES["http"] = args.proxy
    PROXIES["https"] = args.proxy
    ROOT_CA_FILENAME = args.root_ca

    download_parameters = DownloadParameter(args.output_directory, args.platform)
    output_file = download(download_parameters)

    if args.install:
        install(output_file, pathlib.Path(args.install), args.platform)
