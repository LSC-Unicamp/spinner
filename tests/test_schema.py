import pytest
from pydantic import ValidationError

from spinner.schema import SpinnerBenchmark, SpinnerMetadata

# TEST: metadata -----------------------------------------------------------------------


@pytest.fixture
def metadata():
    return {
        "description": "Lorem ipsum dolor sit amet.",
        "version": "1.0",
        "runs": 2,
        "timeout": 5,
        "retry": True,
        "retry_limit": 1,
    }


def test_metadata_valid(metadata):
    """This test should always pass."""
    SpinnerMetadata(**metadata)


# TEST: metadata.version ---------------------------------------------------------------


@pytest.fixture(params=["", "1", "1."])
def metadata_invalid_version(metadata, request):
    metadata["version"] = request.param
    return metadata


def test_metadata_version_invalid(metadata_invalid_version):
    with pytest.raises(ValidationError) as _error:
        SpinnerMetadata(**metadata_invalid_version)


# TEST: metadata.runs ------------------------------------------------------------------


@pytest.fixture(params=[0, -1])
def metadata_invalid_runs(metadata, request):
    metadata["runs"] = request.param
    return metadata


def test_metadata_runs_invalid(metadata_invalid_runs):
    with pytest.raises(ValidationError) as _error:
        SpinnerMetadata(**metadata_invalid_runs)


# TEST: metadata.timeout ---------------------------------------------------------------


@pytest.fixture(params=[0.0, -1.0])
def metadata_invalid_timeout(metadata, request):
    metadata["timeout"] = request.param
    return metadata


def test_metadata_timeout_none(metadata):
    metadata["timeout"] = None
    with pytest.raises(ValidationError):
        SpinnerMetadata(**metadata)


def test_metadata_timeout_invalid(metadata_invalid_timeout):
    with pytest.raises(ValidationError) as _error:
        SpinnerMetadata(**metadata_invalid_timeout)


# TEST: metadata.retry -----------------------------------------------------------------


@pytest.fixture
def metadata_no_retry(metadata):
    metadata.pop("retry", None)
    return metadata


def test_metadata_retry_missing(metadata_no_retry):
    SpinnerMetadata(**metadata_no_retry)


def test_metadata_retry_requires_policy(metadata):
    metadata["timeout"] = None
    metadata["retry"] = 1
    metadata.pop("success_on_return", None)
    metadata.pop("fail_on_return", None)
    with pytest.raises(ValidationError):
        SpinnerMetadata(**metadata)


def test_metadata_success_and_fail_exclusive(metadata):
    metadata["success_on_return"] = [0]
    metadata["fail_on_return"] = [-1]
    with pytest.raises(ValidationError):
        SpinnerMetadata(**metadata)


def test_metadata_is_success_lists():
    md = SpinnerMetadata(
        description="x",
        version="1.0",
        runs=1,
        timeout=1,
        retry=0,
        envvars=[],
        success_on_return=[0, -1],
    )
    assert md.is_success(0)
    assert md.is_success(-1)
    assert not md.is_success(1)

    md = SpinnerMetadata(
        description="x",
        version="1.0",
        runs=1,
        timeout=1,
        retry=0,
        envvars=[],
        fail_on_return=[-1, -6],
    )
    assert md.is_success(0)
    assert not md.is_success(-1)
    assert not md.is_success(-6)


def test_benchmark_zip_basic():
    bench = SpinnerBenchmark(
        {
            "image": ["a", "b"],
            "tb_path": ["p1", "p2"],
            "zip": ["image", "tb_path"],
        }
    )

    combos = bench.sweep_parameters()

    assert combos == [
        {"image": "a", "tb_path": "p1"},
        {"image": "b", "tb_path": "p2"},
    ]
    assert bench.num_jobs == 2


def test_benchmark_zip_with_extra():
    bench = SpinnerBenchmark(
        {
            "image": ["a", "b"],
            "tb_path": ["p1", "p2"],
            "zip": ["image", "tb_path"],
            "kind": ["x", "y"],
        }
    )

    combos = bench.sweep_parameters()
    # zipped pairs cross with other params
    assert len(combos) == 4
    images = {c["image"] for c in combos}
    assert images == {"a", "b"}
    assert bench.num_jobs == 4
