#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from typing import Any, Iterable, List, Mapping, Optional, Union

import pytest as pytest
from airbyte_cdk.models import SyncMode
from airbyte_cdk.sources.declarative.stream_slicers.substream_slicer import SubstreamSlicer
from airbyte_cdk.sources.streams.core import Stream

parent_records = [{"id": 1, "data": "data1"}, {"id": 2, "data": "data2"}]
more_records = [{"id": 10, "data": "data10", "slice": "second_parent"}, {"id": 20, "data": "data20", "slice": "second_parent"}]

data_first_parent_slice = [{"id": 0, "slice": "first", "data": "A"}, {"id": 1, "slice": "first", "data": "B"}]
data_second_parent_slice = [{"id": 2, "slice": "second", "data": "C"}]
data_third_parent_slice = []
all_parent_data = data_first_parent_slice + data_second_parent_slice + data_third_parent_slice
parent_slices = [{"slice": "first"}, {"slice": "second"}, {"slice": "third"}]
second_parent_stream_slice = [{"slice": "second_parent"}]

slice_definition = {"{{ parent_stream_name }}_id": "{{ parent_record['id'] }}", "parent_slice": "{{ parent_stream_slice['slice'] }}"}


class MockStream(Stream):
    def __init__(self, slices, records, name):
        self._slices = slices
        self._records = records
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def primary_key(self) -> Optional[Union[str, List[str], List[List[str]]]]:
        return "id"

    def stream_slices(
        self, *, sync_mode: SyncMode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None
    ) -> Iterable[Optional[Mapping[str, Any]]]:
        yield from self._slices

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        if not stream_slice:
            yield from self._records
        else:
            yield from [r for r in self._records if r["slice"] == stream_slice["slice"]]


@pytest.mark.parametrize(
    "test_name, parent_streams, parent_stream_name_to_slice_key, parent_stream_name_to_stream_slice_key, expected_slices",
    [
        ("test_no_parents", [], {}, {}, []),
        (
            "test_single_parent_slices_no_records",
            [MockStream([{}], [], "first_stream")],
            {"first_stream": "id"},
            {"first_stream": "first_stream_id"},
            [{"first_stream_id": None, "parent_slice": None}],
        ),
        (
            "test_single_parent_slices_with_records",
            [MockStream([{}], parent_records, "first_stream")],
            {"first_stream": "id"},
            {"first_stream": "first_stream_id"},
            [{"first_stream_id": 1, "parent_slice": None}, {"first_stream_id": 2, "parent_slice": None}],
        ),
        (
            "test_with_parent_slices_and_records",
            [MockStream(parent_slices, all_parent_data, "first_stream")],
            {"first_stream": "id"},
            {"first_stream": "first_stream_id"},
            [
                {"parent_slice": "first", "first_stream_id": 0},
                {"parent_slice": "first", "first_stream_id": 1},
                {"parent_slice": "second", "first_stream_id": 2},
                {"parent_slice": "third", "first_stream_id": None},
            ],
        ),
        (
            "test_multiple_parent_streams",
            [
                MockStream(parent_slices, data_first_parent_slice + data_second_parent_slice, "first_stream"),
                MockStream(second_parent_stream_slice, more_records, "second_stream"),
            ],
            {"first_stream": "id", "second_stream": "id"},
            {"first_stream": "first_stream_id", "second_stream": "second_stream_id"},
            [
                {"parent_slice": "first", "first_stream_id": 0},
                {"parent_slice": "first", "first_stream_id": 1},
                {"parent_slice": "second", "first_stream_id": 2},
                {"parent_slice": "third", "first_stream_id": None},
                {"parent_slice": "second_parent", "second_stream_id": 10},
                {"parent_slice": "second_parent", "second_stream_id": 20},
            ],
        ),
    ],
)
def test_substream_slicer(
    test_name, parent_streams, parent_stream_name_to_slice_key, parent_stream_name_to_stream_slice_key, expected_slices
):
    slicer = SubstreamSlicer(parent_streams, parent_stream_name_to_slice_key, parent_stream_name_to_stream_slice_key)
    slices = [s for s in slicer.stream_slices(SyncMode.incremental, stream_state=None)]
    assert slices == expected_slices


@pytest.mark.parametrize(
    "test_name, stream_slice, expected_state",
    [
        ("test_update_cursor_no_state_no_record", {}, None),
        ("test_update_cursor_with_state_single_parent", {"first_stream_id": "1234"}, {"first_stream_id": "1234"}),
        ("test_update_cursor_with_unknown_state_field", {"unknown_stream_id": "1234"}, None),
        (
            "test_update_cursor_with_state_from_both_parents",
            {"first_stream_id": "1234", "second_stream_id": "4567"},
            {"first_stream_id": "1234", "second_stream_id": "4567"},
        ),
    ],
)
def test_update_cursor(test_name, stream_slice, expected_state):
    parent_streams = [
        MockStream(parent_slices, data_first_parent_slice + data_second_parent_slice, "first_stream"),
        MockStream(second_parent_stream_slice, more_records, "second_stream"),
    ]
    parent_stream_name_to_slice_key = {"first_stream": "id", "second_stream": "id"}
    parent_stream_name_to_stream_slice_key = {"first_stream": "first_stream_id", "second_stream": "second_stream_id"}
    slicer = SubstreamSlicer(parent_streams, parent_stream_name_to_slice_key, parent_stream_name_to_stream_slice_key)
    slicer.update_cursor(stream_slice, None)
    updated_state = slicer.get_stream_state()
    assert expected_state == updated_state
