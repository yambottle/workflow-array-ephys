from pynwb.ecephys import ElectricalSeries
import datetime
import time

from element_interface.utils import find_root_directory, find_full_path

from . import (
    dj_config,
    verbose,
    QuietStdOut,
    pipeline,
    test_data,
    lab_csv,
    lab_project_csv,
    lab_user_csv,
    lab_publications_csv,
    lab_keywords_csv,
    lab_protocol_csv,
    lab_project_users_csv,
    ingest_lab,
    subjects_csv,
    ingest_subjects,
    sessions_csv,
    ingest_sessions,
    testdata_paths,
    ephys_insertionlocation,
    kilosort_paramset,
    ephys_recordings,
    clustering_tasks,
    clustering,
    curations,
)

__all__ = [
    "dj_config",
    "pipeline",
    "test_data",
    "lab_csv",
    "lab_project_csv",
    "lab_user_csv",
    "lab_publications_csv",
    "lab_keywords_csv",
    "lab_protocol_csv",
    "lab_project_users_csv",
    "ingest_lab",
    "subjects_csv",
    "ingest_subjects",
    "sessions_csv",
    "ingest_sessions",
    "testdata_paths",
    "ephys_insertionlocation",
    "kilosort_paramset",
    "ephys_recordings",
    "clustering_tasks",
    "clustering",
    "curations",
]

from workflow_array_ephys.export import (
    ecephys_session_to_nwb,
    session_to_nwb,
    write_nwb,
)


def test_session_to_nwb(pipeline, ingest_lab, ingest_subjects, ingest_sessions):
    session_kwargs = {
        "session_key": {
            "subject": "subject5",
            "session_datetime": datetime.datetime(2018, 7, 3, 20, 32, 28),
        },
        "lab_key": {"lab": "LabA"},
        "protocol_key": {"protocol": "ProtA"},
        "project_key": {"project": "ProjA"},
    }

    if verbose:
        nwbfile = session_to_nwb(**session_kwargs)
    else:
        with QuietStdOut():
            nwbfile = session_to_nwb(**session_kwargs)

    assert nwbfile.session_id == "subject5_2018-07-03T20:32:28"
    assert nwbfile.session_description == "Successful data collection"
    # when saved in NWB, converts local to UTC
    assert nwbfile.session_start_time == datetime.datetime(
        2018, 7, 3, 20, 32, 28
    ).astimezone(datetime.timezone.utc)
    assert nwbfile.experimenter == ["User1"]

    assert nwbfile.subject.subject_id == "subject5"
    assert nwbfile.subject.sex == "F"

    assert nwbfile.institution == "Example Uni"
    assert nwbfile.lab == "The Example Lab"

    assert nwbfile.protocol == "ProtA"
    assert nwbfile.notes == "Protocol for managing data ingestion"

    assert nwbfile.experiment_description == "Example project to populate element-lab"


def test_write_to_nwb(
    pipeline,
    ingest_lab,
    ingest_subjects,
    ingest_sessions,
    ephys_insertionlocation,
    kilosort_paramset,
    ephys_recordings,
    clustering_tasks,
    clustering,
    curations,
):
    ephys = pipeline["ephys"]

    session_key = dict(subject="subject5", session_datetime="2018-07-03 20:32:28")

    ephys.LFP.populate(session_key, display_progress=verbose)
    ephys.CuratedClustering.populate(session_key, display_progress=verbose)
    ephys.WaveformSet.populate(session_key, display_progress=verbose)

    ecephys_kwargs = {
        "session_key": session_key,
        "raw": True,
        "spikes": True,
        "lfp": "dj",
    }

    if verbose:
        nwbfile = ecephys_session_to_nwb(**ecephys_kwargs)
    else:
        with QuietStdOut():
            nwbfile = ecephys_session_to_nwb(**ecephys_kwargs)

    root_dirs = pipeline["get_ephys_root_data_dir"]()
    root_dir = find_root_directory(
        root_dirs,
        find_full_path(
            root_dirs,
            (pipeline["session"].SessionDirectory & session_key).fetch1("session_dir"),
        ),
    )

    write_nwb(nwbfile, root_dir / time.strftime("_test_%Y%m%d-%H%M%S.nwb"))


def test_convert_to_nwb(
    pipeline,
    ingest_lab,
    ingest_subjects,
    ingest_sessions,
    ephys_insertionlocation,
    kilosort_paramset,
    ephys_recordings,
    clustering_tasks,
    clustering,
    curations,
):
    ephys = pipeline["ephys"]

    session_key = dict(subject="subject5", session_datetime="2018-07-03 20:32:28")

    ephys.CuratedClustering.populate(session_key, display_progress=verbose)
    ephys.WaveformSet.populate(session_key, display_progress=verbose)

    ecephys_kwargs = {
        "session_key": session_key,
        "end_frame": 1000,
        "spikes": True,
        "lab_key": {"lab": "LabA"},
        "protocol_key": {"protocol": "ProtA"},
        "project_key": {"project": "ProjA"},
    }

    if verbose:
        nwbfile = ecephys_session_to_nwb(**ecephys_kwargs)
    else:
        with QuietStdOut():
            nwbfile = ecephys_session_to_nwb(**ecephys_kwargs)

    for x in ("262716621", "714000838"):
        assert x in nwbfile.devices

    assert len(nwbfile.electrodes) == 1920
    for col in ("shank", "shank_row", "shank_col"):
        assert col in nwbfile.electrodes

    for es_name in ("ElectricalSeries1", "ElectricalSeries2"):
        es = nwbfile.acquisition[es_name]
        assert isinstance(es, ElectricalSeries)
        assert es.conversion == 2.34375e-06

    # make sure the ElectricalSeries objects don't share electrodes
    assert not set(nwbfile.acquisition["ElectricalSeries1"].electrodes.data) & set(
        nwbfile.acquisition["ElectricalSeries2"].electrodes.data
    )

    assert len(nwbfile.units) == 499

    for col in ("cluster_quality_label", "spike_depths"):
        assert col in nwbfile.units

    for es_name in ("ElectricalSeries1", "ElectricalSeries2"):
        es = nwbfile.processing["ecephys"].data_interfaces["LFP"][es_name]
        assert isinstance(es, ElectricalSeries)
        assert es.conversion == 4.6875e-06
        assert es.rate == 2500.0
