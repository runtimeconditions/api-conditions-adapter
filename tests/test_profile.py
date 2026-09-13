import pathlib

from api_conditions_adapter.profile import api_conditions, load_profile, source_component_name

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_load_profile_reads_yaml():
    profile = load_profile(FIXTURES / "request-coordinator.yaml")
    assert profile["metadata"]["name"] == "request-coordinator"


def test_api_conditions_filters_out_non_api_conditions():
    profile = load_profile(FIXTURES / "request-coordinator.yaml")
    conditions = api_conditions(profile)
    names = {c["name"] for c in conditions}
    assert names == {"available-stock-capability", "delivery-work-capability"}


def test_source_component_name():
    profile = load_profile(FIXTURES / "request-coordinator.yaml")
    assert source_component_name(profile) == "request-coordinator"
