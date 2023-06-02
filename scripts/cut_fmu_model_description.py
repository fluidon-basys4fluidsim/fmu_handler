import json
import fnmatch
from pathlib import Path
from typing import Union, List, Optional
from fmu_handler.fmu_adapter import FMUAdapter
from fmu_handler.fmu_types import FMUScalarVariable, Causality
from utils.custom_file_handling import check_create_directory_path


def _cut_fmu_model_description_with_positive_list(keep_list: List, delete_list: List, fmu: FMUAdapter)\
        -> FMUAdapter:
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


def reduce_fmu_model_descriptions_in_directory(dir_path: Union[str, Path], output_suffix: Optional[str] = "reduced"):
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path {dir_path} is not a directory.")

    if not output_suffix:
        output_suffix = ""
    elif not output_suffix.startswith("_"):
        output_suffix = f"_{output_suffix}"

    with open("./parameter_reduction_config.json", "r") as config_file:
        config_data = json.load(config_file)
        config_file.close()

    keep_list = config_data.get("keep_elements", [])
    delete_list = config_data.get("delete_elements", [])
    for fmu_file in dir_path.iterdir():
        if fmu_file.suffix == ".fmu":
            fmu = FMUAdapter(fmu_file=fmu_file)
            fmu = _cut_fmu_model_description_with_positive_list(
                keep_list=keep_list, delete_list=delete_list, fmu=fmu
            )
            save_dir_path = check_create_directory_path(dir_path=dir_path.joinpath("reduced"), create=True)
            fmu.save_fmu_copy(file_name=f"{fmu_file.stem}{output_suffix}", tar_dir_path=save_dir_path)


if __name__ == "__main__":
    reduce_fmu_model_descriptions_in_directory(dir_path="./", output_suffix=None)
