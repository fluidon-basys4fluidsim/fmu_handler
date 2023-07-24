from pathlib import Path
from fmu_handler.fmu_adapter import log
from fmu_handler.handler_functions import reduce_fmu_model_descriptions_in_directory

if __name__ == "__main__":
    log.setLevel("INFO")
    fmu_dir = Path(__file__).parent.parent.joinpath("data", "fmu_par_red")
    reduce_fmu_model_descriptions_in_directory(fmu_dir=fmu_dir, output_dir=fmu_dir.joinpath("reduced"))
