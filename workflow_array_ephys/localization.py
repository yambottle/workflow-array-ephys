import datajoint as dj
from element_interface.utils import find_full_path
from element_electrode_localization import coordinate_framework, electrode_localization
from element_electrode_localization.coordinate_framework import load_ccf_annotation


from .pipeline import ephys, probe
from .paths import (
    get_ephys_root_data_dir,
    get_session_directory,
    get_electrode_localization_dir,
)


if "custom" not in dj.config:
    dj.config["custom"] = {}

db_prefix = dj.config["custom"].get("database.prefix", "")

__all__ = [
    "ephys",
    "probe",
    "coordinate_framework",
    "electrode_localization",
    "ProbeInsertion",
    "get_ephys_root_data_dir",
    "get_session_directory",
    "get_electrode_localization_dir",
    "load_ccf_annotation",
]

ccf_id = 0  # Atlas ID
voxel_resolution = 100

# Activate "electrode-localization" schema ------------------------------------

ProbeInsertion = ephys.ProbeInsertion

electrode_localization.activate(
    db_prefix + "electrode_localization", db_prefix + "ccf", linking_module=__name__
)

nrrd_filepath = find_full_path(
    get_ephys_root_data_dir(), f"annotation_{voxel_resolution}.nrrd"
)
ontology_csv_filepath = find_full_path(get_ephys_root_data_dir(), "query.csv")

if (
    not (coordinate_framework.CCF & {"ccf_id": ccf_id})
    and nrrd_filepath.exists()
    and ontology_csv_filepath.exists()
):
    coordinate_framework.load_ccf_annotation(
        ccf_id=ccf_id,
        version_name="ccf_2017",
        voxel_resolution=voxel_resolution,
        nrrd_filepath=nrrd_filepath,
        ontology_csv_filepath=ontology_csv_filepath,
    )
