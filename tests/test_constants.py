from p2000c_disk import constants


def test_geometry_is_internally_consistent() -> None:
    assert constants.IMAGE_SIZE == constants.SECTOR_SIZE * constants.SECTOR_COUNT
    assert constants.SYSTEM_AREA_END_LBA == 31
    assert constants.DIRECTORY_START_LBA == 7_840
    assert constants.DIRECTORY_ENTRY_COUNT == 256
    assert constants.FIRST_OBSERVED_FILE_DATA_LBA == 7_904


def test_unknown_region_is_not_named_as_metadata() -> None:
    assert constants.UNKNOWN_REGION_START_LBA == 32
    assert constants.UNKNOWN_REGION_END_LBA == 7_839

