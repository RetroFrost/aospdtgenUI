#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from argparse import ArgumentParser
from pathlib import Path
from sebaubuntu_libs.liblocale import setup_locale
from sebaubuntu_libs.liblogging import setup_logging

from aospdtgen import current_path
from aospdtgen.device_tree import DeviceTree


def main():
    setup_logging()

    parser = ArgumentParser(description="Android device tree generator")
    parser.add_argument(
        "dump_path",
        nargs="?",
        type=Path,
        help="path to an Android dump made with dumpyara",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=current_path / "output", help="custom output folder"
    )
    parser.add_argument(
        "--no-proprietary-files",
        action="store_true",
        help="Don't generate the proprietary files list and the extract-files script",
    )
    parser.add_argument(
        "--dual-support",
        action="store_true",
        help="Enable simultaneous ROM and Custom Recovery support",
    )
    parser.add_argument(
        "--ota-url",
        help="OTA URL for the device",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI",
    )

    args = parser.parse_args()

    if args.gui or args.dump_path is None:
        from aospdtgen.gui import main as gui_main
        gui_main()
        return

    setup_locale()

    dump = DeviceTree(
        args.dump_path,
        no_proprietary_files=args.no_proprietary_files,
        dual_support=args.dual_support,
        ota_url=args.ota_url,
    )
    dump.dump_to_folder(args.output)
    dump.cleanup()

    print(f"\nDone! You can find the device tree in {str(args.output)}")
