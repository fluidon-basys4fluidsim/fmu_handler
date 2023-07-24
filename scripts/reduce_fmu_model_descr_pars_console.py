#!/usr/bin/env python3

"""
Script to cut the model description of fmus in a directory. The model description is cut according to the
parameter_reduction_config.json file in the directory. If no output directory or suffix is specified, the original
fmus are overwritten.
"""

import argparse
import logging
from pathlib import Path
from fmu_handler.handler_functions import reduce_fmu_model_descriptions_in_directory


def reduce_model_descriptions_in_directory_console():
    """
    Console script to cut the model description of fmus in a directory. The model description is cut according to the
    parameter_reduction_config.json file in the directory. If no output directory or suffix is specified, the original
    fmus are overwritten.
    :return:
    """
    parser = argparse.ArgumentParser(
        description="Reduce the model description of all fmus in a directory according to the "
                    "parameter_reduction_config.json file in the directory."
    )
    parser.add_argument(
        "fmu_dir", type=str, default=None,
        help="Path to the directory containing the fmus."
    )
    parser.add_argument(
        "-o", "--output_path", type=str, default=None,
        help="If None, the reduced fmus are saved and possibly overwritten in the same directory as the original ones."
    )
    parser.add_argument(
        "-s", "--output_suffix", type=str, default=None,
        help="If None, the reduced fmus are saved and possibly overwritten. Otherwise, the suffix is added to the "
             "modified fmu files."
    )

    args = parser.parse_args()

    if args.fmu_dir is None:
        fmu_dir = Path.cwd()
    else:
        fmu_dir = Path(args.fmu_dir)

    reduce_fmu_model_descriptions_in_directory(
        fmu_dir=fmu_dir, output_dir=args.output_path, output_suffix=args.output_suffix
    )


if __name__ == "__main__":
    log = logging.getLogger("fmu_handler")
    log.setLevel("INFO")
    reduce_model_descriptions_in_directory_console()
