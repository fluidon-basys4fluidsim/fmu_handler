#!/usr/bin/env python3

"""
Script to cut the model description of fmus in a directory. The model description is cut according to the
parameter_reduction_config.json file in the directory. If no output directory or suffix is specified, the original
fmus are overwritten.

Usage:


"""

import argparse
import json
import fnmatch
from pathlib import Path
from typing import Union, List, Optional
from fmu_handler.fmu_adapter import FMUAdapter
from fmu_handler.fmu_types import FMUScalarVariable, Causality
from utils.custom_file_handling import check_create_directory_path


def _cut_fmu_model_description_with_lists(keep_list: List, delete_list: List, fmu: FMUAdapter)\
        -> FMUAdapter:
    """
    Function to delete defined elements.

    Generally, all elements are selected not to be deleted.
    First, all elements that fit to the delete_list are tagged to be deleted.
    Then, elements to be kept might untag those again.
    Finally, all tagged scalar variables are deleted from the fmu model description xml.

    :param keep_list: Elements that should be kept.
    :param delete_list: Elements that should be deleted.
    :param fmu: FMUAdapter object.
    :return:
    """
    for scalar_variable in fmu.query_scalar_variables(query=FMUScalarVariable(causality=Causality.parameter)):
        delete = False
        for negative_element in delete_list:
            if fnmatch.fnmatch(scalar_variable.name, negative_element):
                delete = True
        for positive_element in keep_list:
            if fnmatch.fnmatch(scalar_variable.name, positive_element):
                delete = False
        if delete:
            fmu.remove_scalar_variable_by_name(name=scalar_variable.name)
    return fmu


def reduce_fmu_model_descriptions_in_directory(dir_path: Union[str, Path],
                                               output_path: Optional[Union[str, Path]] = None,
                                               output_suffix: Optional[str] = None):
    """
    According to the parameter_reduction_config.json file in the directory, the model description of all fmus in this
    directory are reduced.

    :param dir_path: Path to the directory containing the fmus.
    :param output_path: If None, the reduced fmus are saved and possibly overwritten
    in the same directory as the original ones.
    :param output_suffix: If None, the reduced fmus are saved and possibly overwritten. Otherwise, the suffix is added
    to the modified fmu files.
    :return:
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path {dir_path} is not a directory.")

    if not output_suffix:
        output_suffix = ""
    elif not output_suffix.startswith("_"):
        output_suffix = f"_{output_suffix}"

    with open(dir_path.joinpath("parameter_reduction_config.json"), "r") as config_file:
        config_data = json.load(config_file)
        config_file.close()

    keep_list = config_data.get("keep_elements", [])
    delete_list = config_data.get("delete_elements", [])
    for fmu_file in dir_path.iterdir():
        if fmu_file.suffix == ".fmu":
            fmu = FMUAdapter(fmu_file=fmu_file)
            fmu = _cut_fmu_model_description_with_lists(
                keep_list=keep_list, delete_list=delete_list, fmu=fmu
            )

            if output_path is not None:
                save_dir_path = check_create_directory_path(dir_path=output_path)
            else:
                save_dir_path = dir_path

            fmu.save_fmu(file_name=f"{fmu_file.stem}{output_suffix}", tar_dir_path=save_dir_path)


def reduce_model_descriptions_in_directory_console():
    parser = argparse.ArgumentParser(
        description="Reduce the model description of all fmus in a directory according to the "
                    "parameter_reduction_config.json file in the directory."
    )
    parser.add_argument(
        "dir_path", type=str, default=Path.cwd(),
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
    if not args.dir_path:
        raise ValueError("No directory path specified.")
    reduce_fmu_model_descriptions_in_directory(
        dir_path=args.dir_path, output_path=args.output_path, output_suffix=args.output_suffix
    )


if __name__ == "__main__":
    reduce_model_descriptions_in_directory_console()
