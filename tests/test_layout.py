from __future__ import annotations

from p2000c_disk import constants
from p2000c_disk.layout import decode_dpb, find_matching_dpbs


def _dpb_bytes() -> bytes:
    return (
        constants.DPB_SECTORS_PER_TRACK.to_bytes(2, "little")
        + bytes(
            [
                constants.DPB_BLOCK_SHIFT,
                constants.DPB_BLOCK_MASK,
                constants.DPB_EXTENT_MASK,
            ]
        )
        + constants.DPB_MAXIMUM_BLOCK.to_bytes(2, "little")
        + constants.DPB_MAXIMUM_DIRECTORY_ENTRY.to_bytes(2, "little")
        + bytes(constants.DPB_ALLOCATION_RESERVED)
        + constants.DPB_DIRECTORY_CHECK_SIZE.to_bytes(2, "little")
        + constants.DPB_RESERVED_TRACKS.to_bytes(2, "little")
    )


def test_decode_and_find_confirmed_dpb() -> None:
    system = b"prefix" + _dpb_bytes() + b"suffix"
    decoded = decode_dpb(system, 6)
    assert decoded.matches_p2000c_layout
    assert find_matching_dpbs(system) == (decoded,)


def test_different_dpb_does_not_match() -> None:
    system = bytearray(_dpb_bytes())
    system[2] = 4
    assert not decode_dpb(bytes(system), 0).matches_p2000c_layout
    assert find_matching_dpbs(bytes(system)) == ()
