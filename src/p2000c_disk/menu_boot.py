"""Controlled menu startup for the two bundled, 62K Philips CP/M BIOS layouts.

The BIOS reloads CCP/BDOS at D680 before relocating them to DC00. Its warm
reload continuation normally jumps to F269. Redirect it through two seven-byte helpers
in the unused end of the freshly loaded CCP command buffer: clear the source
command length at D687 for a deliberate exit, or select A: user 0 while
retaining A:MENU after an application, then continue the original relocation. Cold startup
never takes this path. No resident menu code or disk writes are needed.
"""
WARM_JUMP = 0x16E6
HELPER = 0xC0
ORIGINAL = bytes.fromhex("c369f2")
REDIRECT = bytes.fromhex("c3c0d6")
CODE = bytes.fromhex(
    "af3287d6c369f2"  # Deliberate menu exit: clear startup command.
    "af320400c369f2"  # Program return: select A: user 0, retain command.
)


def is_menu_boot(system: bytes) -> bool:
    return (system[WARM_JUMP:WARM_JUMP + 3] == REDIRECT
            and system[HELPER:HELPER + len(CODE)] == CODE)


def original_menu_system(system: bytes) -> bytes:
    if not is_menu_boot(system):
        return system
    data = bytearray(system)
    data[WARM_JUMP:WARM_JUMP + 3] = ORIGINAL
    data[HELPER:HELPER + len(CODE)] = bytes(len(CODE))
    return bytes(data)


def cold_menu_boot(system: bytes) -> bytes:
    if (len(system) != 8192 or system[128:134] != bytes.fromhex("c35cdfc358df")
            or system[WARM_JUMP - 2:WARM_JUMP + 15] !=
            bytes.fromhex("edb0c369f2217fec11fff1010016edb821")
            or any(system[HELPER:264])):
        raise ValueError("Menu startup requires the verified Philips 62K warm-reload layout")
    data = bytearray(system)
    data[WARM_JUMP:WARM_JUMP + 3] = REDIRECT
    data[HELPER:HELPER + len(CODE)] = CODE
    return bytes(data)
