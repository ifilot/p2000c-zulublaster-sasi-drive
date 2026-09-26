"""Profile-driven inspection and guarded editing of boot configuration fields."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import os
from pathlib import Path
import shutil
import tempfile
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping, Sequence

from . import constants
from .image import DiskImage
from .layout import find_matching_dpbs
from .menu_boot import is_menu_boot, original_menu_system
from .verify import require_valid_image


Confidence = Literal["confirmed", "high", "inferred", "unknown"]
LayoutStatus = Literal["recognized", "partially recognized", "unknown"]


class ConfigError(ValueError):
    """Base class for boot-configuration errors."""


class UnknownSystemLayoutError(ConfigError):
    """Raised when no supported system layout can be recognized safely."""


class UnsupportedConfigEditError(ConfigError):
    """Raised when evidence is insufficient to edit a requested field."""


class ConfigValueError(ConfigError):
    """Raised for a setting value that cannot be encoded safely."""


class ConfigConsistencyError(ConfigError):
    """Raised when related configuration representations disagree."""


@dataclass(frozen=True, slots=True)
class ConfigCopy:
    name: str
    offset: int
    size: int
    encoding: str
    padding_byte: int = 0
    expected_bytes: bytes | None = None


@dataclass(frozen=True, slots=True)
class ConfigField:
    name: str
    offset: int
    size: int
    encoding: str
    expected_bytes: bytes | None
    confidence: Confidence
    writable: bool = False
    length_offset: int | None = None
    capacity: int | None = None
    padding_byte: int = 0
    allow_length_change: bool = False
    clear_supported: bool = False
    bit_mask: int | None = None
    enabled_value: int | None = None
    disabled_value: int | None = None
    unit_seconds: int = 1
    copies: tuple[ConfigCopy, ...] = ()
    allowed_command_separators: str = ""


@dataclass(frozen=True, slots=True)
class SystemLayoutProfile:
    name: str
    image_size: int
    system_area_size: int
    known_system_hashes: frozenset[str]
    fields: Mapping[str, ConfigField]
    recognizer: Callable[[bytes], bool]
    partial_recognizer: Callable[[bytes], bool]


@dataclass(frozen=True, slots=True)
class FieldSource:
    name: str
    offset: int
    size: int
    raw_hex: str
    decoded_value: str | int | bool | None
    required_copy: bool


@dataclass(frozen=True, slots=True)
class DecodedConfigField:
    name: str
    value: str | int | bool | None
    confidence: Confidence
    writable: bool
    consistent: bool
    sources: tuple[FieldSource, ...]


@dataclass(frozen=True, slots=True)
class ConfigLayoutCandidate:
    kind: str
    offset: int
    size: int
    raw_hex: str
    decoded_value: str
    confidence: Confidence
    evidence: str


@dataclass(frozen=True, slots=True)
class ConfigInspection:
    path: str
    layout_status: LayoutStatus
    profile_name: str | None
    known_hash_match: bool
    system_area_sha256: str
    fields: Mapping[str, DecodedConfigField]
    boot_drive_configuration: str | None
    layout_candidates: tuple[ConfigLayoutCandidate, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "configuration_layout": self.layout_status,
            "profile": self.profile_name,
            "known_hash_match": self.known_hash_match,
            "system_area_sha256": self.system_area_sha256,
            "decoded_values": {
                name: asdict(field) for name, field in self.fields.items()
            },
            "boot_drive_configuration": self.boot_drive_configuration,
            "layout_candidates": [asdict(item) for item in self.layout_candidates],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ConfigUpdates:
    capslock: bool | None = None
    printer_timeout: int | None = None
    autostart: str | None = None
    clear_autostart: bool = False
    welcome: str | None = None
    clear_welcome: bool = False

    @property
    def has_changes(self) -> bool:
        return any(
            (
                self.capslock is not None,
                self.printer_timeout is not None,
                self.autostart is not None,
                self.clear_autostart,
                self.welcome is not None,
                self.clear_welcome,
            )
        )


@dataclass(frozen=True, slots=True)
class ConfigPatch:
    field_name: str
    offset: int
    old_bytes: bytes
    new_bytes: bytes
    current_value: str | int | bool | None
    new_value: str | int | bool | None
    reason: str

    @property
    def end_offset(self) -> int:
        return self.offset + len(self.old_bytes) - 1


@dataclass(frozen=True, slots=True)
class ConfigPatchPlan:
    source: str
    profile_name: str
    patches: tuple[ConfigPatch, ...]
    requested_printer_timeout: int | None
    effective_printer_timeout: int | None
    warnings: tuple[str, ...]


def _p2000c_recognizer(
    welcome_size: int, keyboard_offset: int, drive_offset: int
) -> Callable[[bytes], bool]:
    def recognize(system: bytes) -> bool:
        welcome = system[6_838 : 6_838 + welcome_size]
        return (
            len(system) == constants.SYSTEM_AREA_SIZE
            and bool(find_matching_dpbs(system))
            and system[128:134] == bytes.fromhex("c35ce3c358e3")
            and system[134] == 0x7F
            and system[6803:6817] == b"PHILIPS P2000C"
            and all(0x20 <= byte <= 0x7E for byte in welcome)
            and system[6_838 + welcome_size : keyboard_offset] == b"\r\n\n"
            and system[keyboard_offset : keyboard_offset + 8] == b"KEYBOARD"
            and system[drive_offset : drive_offset + 2] == b"A:"
            and system[6716:6727] == b"CONFIG  COM"
        )

    return recognize


def _p2000c_partial_recognizer(system: bytes) -> bool:
    return bool(find_matching_dpbs(system)) or any(
        marker in system
        for marker in (b"PHILIPS P2000C", b"A:8MB-HRD1", b"CONFIG  COM")
    )


P2000C_BOOT_PROFILE = SystemLayoutProfile(
    name="p2000c-config-generated-v1",
    image_size=constants.IMAGE_SIZE,
    system_area_size=constants.SYSTEM_AREA_SIZE,
    known_system_hashes=frozenset(
        {"7609d9936d1d3520c04b3a365c855954efae01b11c7fc4a022fea3526b536409"}
    ),
    fields=MappingProxyType(
        {
            "autostart": ConfigField(
                name="autostart",
                offset=136,
                size=128,
                encoding="length-prefixed-ascii",
                expected_bytes=None,
                confidence="confirmed",
                writable=True,
                length_offset=135,
                capacity=127,
                padding_byte=0,
                allow_length_change=True,
                clear_supported=True,
                allowed_command_separators="",
            ),
            "welcome_message": ConfigField(
                name="welcome_message",
                offset=6_838,
                size=9,
                encoding="fixed-ascii",
                expected_bytes=b"Hello Ivo",
                confidence="confirmed",
                writable=True,
                allow_length_change=False,
                clear_supported=False,
            ),
            "boot_drive_configuration": ConfigField(
                name="boot_drive_configuration",
                offset=6_896,
                size=10,
                encoding="fixed-ascii",
                expected_bytes=b"A:8MB-HRD1",
                confidence="confirmed",
            ),
        }
    ),
    recognizer=_p2000c_recognizer(9, 6_850, 6_896),
    partial_recognizer=_p2000c_partial_recognizer,
)

P2000C_FILES_PROFILE = SystemLayoutProfile(
    name="p2000c-config-generated-v1-welcome-12",
    image_size=constants.IMAGE_SIZE,
    system_area_size=constants.SYSTEM_AREA_SIZE,
    known_system_hashes=frozenset(
        {"6edc5205ce2c974bdc8571b35689d7fe29ccae23f464fbf29a00e25c0fd3c76b"}
    ),
    fields=MappingProxyType(
        {
            "autostart": ConfigField(
                name="autostart",
                offset=136,
                size=128,
                encoding="length-prefixed-ascii",
                expected_bytes=None,
                confidence="confirmed",
                writable=True,
                length_offset=135,
                capacity=127,
                padding_byte=0,
                allow_length_change=True,
                clear_supported=True,
                allowed_command_separators="",
            ),
            "welcome_message": ConfigField(
                name="welcome_message",
                offset=6_838,
                size=12,
                encoding="fixed-ascii",
                expected_bytes=b"Hello P2000C",
                confidence="confirmed",
                writable=True,
                allow_length_change=False,
                clear_supported=False,
            ),
            "boot_drive_configuration": ConfigField(
                name="boot_drive_configuration",
                offset=6_899,
                size=10,
                encoding="fixed-ascii",
                expected_bytes=b"A:8MB-HRD1",
                confidence="confirmed",
            ),
        }
    ),
    recognizer=_p2000c_recognizer(12, 6_853, 6_899),
    partial_recognizer=_p2000c_partial_recognizer,
)


def _p2000c_split_recognizer(system: bytes) -> bool:
    welcome = system[6_909:6_921]
    return (
        len(system) == constants.SYSTEM_AREA_SIZE
        and len(find_matching_dpbs(system)) == 2
        and system[128:134] == bytes.fromhex("c35cdfc358df")
        and system[134] == 0x7F
        and system[6_874:6_888] == b"PHILIPS P2000C"
        and all(0x20 <= byte <= 0x7E for byte in welcome)
        and system[6_921:6_924] == b"\r\n\n"
        and system[6_924:6_932] == b"KEYBOARD"
        and system[6_970:6_972] == b"A:"
        and system[6_787:6_798] == b"CONFIG  COM"
    )


P2000C_SPLIT_PROFILE = SystemLayoutProfile(
    name="p2000c-config-generated-v1-split-low-high",
    image_size=constants.IMAGE_SIZE,
    system_area_size=constants.SYSTEM_AREA_SIZE,
    known_system_hashes=frozenset(
        {"d5657fa88bffc30f3f52bba3fcd6b46f0c26cbb7e31f1b6a7e88a6c695f69ab5"}
    ),
    fields=MappingProxyType(
        {
            "autostart": ConfigField(
                name="autostart",
                offset=136,
                size=128,
                encoding="length-prefixed-ascii",
                expected_bytes=None,
                confidence="confirmed",
                writable=True,
                length_offset=135,
                capacity=127,
                padding_byte=0,
                allow_length_change=True,
                clear_supported=True,
                allowed_command_separators="",
            ),
            "welcome_message": ConfigField(
                name="welcome_message",
                offset=6_909,
                size=12,
                encoding="fixed-ascii",
                expected_bytes=b"Hello P2000C",
                confidence="confirmed",
                writable=True,
                allow_length_change=False,
                clear_supported=False,
            ),
            "boot_drive_configuration": ConfigField(
                name="boot_drive_configuration",
                offset=6_970,
                size=10,
                encoding="fixed-ascii",
                expected_bytes=b"A:5MB-HRD1",
                confidence="confirmed",
            ),
        }
    ),
    recognizer=_p2000c_split_recognizer,
    partial_recognizer=_p2000c_partial_recognizer,
)

COBOARD_SYSTEM_SHA256 = "401a12434c78dcb766e2de342dc8c6503b622827989cf21f2ec027076236bc54"


def _p2000c_coboard_recognizer(system: bytes) -> bool:
    # This combined system has a different BIOS layout. Only the confirmed
    # CCP autostart buffer is editable; every other byte must match the
    # CONFIG-generated system with the recovered CoPower initializer.
    if len(system) != constants.SYSTEM_AREA_SIZE:
        return False
    normalized = bytearray(system)
    normalized[135:264] = bytes(129)
    return sha256(normalized).hexdigest() == COBOARD_SYSTEM_SHA256


P2000C_COBOARD_PROFILE = SystemLayoutProfile(
    name="p2000c-sasi-coboard-recovered-v1",
    image_size=constants.IMAGE_SIZE,
    system_area_size=constants.SYSTEM_AREA_SIZE,
    known_system_hashes=frozenset({COBOARD_SYSTEM_SHA256}),
    fields=MappingProxyType({"autostart": P2000C_SPLIT_PROFILE.fields["autostart"]}),
    recognizer=_p2000c_coboard_recognizer,
    partial_recognizer=_p2000c_partial_recognizer,
)


# The menu warm-start helper occupies the unused tail of the command buffer.
# Keep it outside the editable field, including when clearing autostart.
MENU_AUTOSTART = replace(P2000C_SPLIT_PROFILE.fields["autostart"], size=56, capacity=55)
P2000C_MENU_PROFILE = replace(
    P2000C_SPLIT_PROFILE, name="p2000c-menu-cold-start-v1",
    fields=MappingProxyType({**P2000C_SPLIT_PROFILE.fields, "autostart": MENU_AUTOSTART}),
    recognizer=lambda system: is_menu_boot(system) and
        _p2000c_split_recognizer(original_menu_system(system)),
)
P2000C_MENU_COBOARD_PROFILE = replace(
    P2000C_COBOARD_PROFILE, name="p2000c-menu-coboard-cold-start-v1",
    fields=MappingProxyType({"autostart": MENU_AUTOSTART}),
    recognizer=lambda system: is_menu_boot(system) and
        _p2000c_coboard_recognizer(original_menu_system(system)),
)


KNOWN_SYSTEM_PROFILES: tuple[SystemLayoutProfile, ...] = (
    P2000C_MENU_PROFILE,
    P2000C_MENU_COBOARD_PROFILE,
    P2000C_BOOT_PROFILE,
    P2000C_FILES_PROFILE,
    P2000C_SPLIT_PROFILE,
    P2000C_COBOARD_PROFILE,
)


def _layout_candidates(system: bytes) -> tuple[ConfigLayoutCandidate, ...]:
    """Describe candidates without promoting them to editable fields."""
    candidates: list[ConfigLayoutCandidate] = []
    offset = 0
    while offset < len(system) - 10:
        capacity = system[offset]
        length = system[offset + 1]
        storage_size = capacity + 1
        end = offset + 2 + storage_size
        if not 8 <= capacity <= 127 or length > capacity or end > len(system):
            offset += 1
            continue
        raw_value = system[offset + 2 : offset + 2 + length]
        padding = system[offset + 2 + length : end]
        if any(byte < 0x20 or byte > 0x7E for byte in raw_value) or any(padding):
            offset += 1
            continue
        candidates.append(
            ConfigLayoutCandidate(
                kind="length-prefixed-zero-padded-ascii",
                offset=offset,
                size=2 + storage_size,
                raw_hex=system[offset:end].hex().upper(),
                decoded_value=raw_value.decode("ascii"),
                confidence="high" if offset == 134 else "inferred",
                evidence=(
                    f"capacity={capacity}, length={length}, printable text, "
                    f"and {len(padding)} zero padding byte(s)"
                ),
            )
        )
        offset = end
    return tuple(candidates)


def _unknown_field(name: str) -> DecodedConfigField:
    return DecodedConfigField(
        name=name,
        value=None,
        confidence="unknown",
        writable=False,
        consistent=False,
        sources=(),
    )


def _decode_ascii(raw: bytes, padding_byte: int) -> str | None:
    unpadded = raw.rstrip(bytes([padding_byte]))
    if any(value < 0x20 or value > 0x7E for value in unpadded):
        return None
    return unpadded.decode("ascii")


def _decode_field(
    system: bytes, field: ConfigField
) -> tuple[DecodedConfigField, tuple[str, ...]]:
    warnings: list[str] = []
    raw = system[field.offset : field.offset + field.size]
    sources: list[FieldSource] = []
    if field.encoding == "length-prefixed-ascii":
        if field.length_offset is None:
            raise ConfigError(f"profile field {field.name} has no length offset")
        length = system[field.length_offset]
        capacity = field.capacity if field.capacity is not None else field.size
        if length > capacity or length > field.size:
            value: str | int | bool | None = None
            warnings.append(
                f"{field.name} length {length} exceeds capacity {capacity}"
            )
        else:
            value = _decode_ascii(raw[:length], field.padding_byte)
            if value is None:
                warnings.append(f"{field.name} contains non-printable ASCII")
            expected_padding = bytes([field.padding_byte]) * (field.size - length)
            if raw[length:] != expected_padding:
                warnings.append(f"{field.name} has unexpected field padding")
        sources.append(
            FieldSource(
                name=f"{field.name}_length",
                offset=field.length_offset,
                size=1,
                raw_hex=system[field.length_offset : field.length_offset + 1].hex().upper(),
                decoded_value=length,
                required_copy=True,
            )
        )
    elif field.encoding == "fixed-ascii":
        value = _decode_ascii(raw, field.padding_byte)
        if value is None:
            warnings.append(f"{field.name} contains non-printable ASCII")
    elif field.encoding == "bitmask-flag":
        if field.bit_mask is None:
            raise ConfigError(f"profile field {field.name} has no bit mask")
        masked = raw[0] & field.bit_mask
        if masked == field.enabled_value:
            value = True
        elif masked == field.disabled_value:
            value = False
        else:
            value = None
            warnings.append(f"{field.name} has unknown flag value 0x{masked:02X}")
    elif field.encoding == "uint-le-units":
        value = int.from_bytes(raw, "little") * field.unit_seconds
    else:
        raise ConfigError(f"unsupported profile encoding: {field.encoding}")

    sources.append(
        FieldSource(
            name=field.name,
            offset=field.offset,
            size=field.size,
            raw_hex=raw.hex().upper(),
            decoded_value=value,
            required_copy=True,
        )
    )
    consistent = value is not None
    for copy in field.copies:
        copy_raw = system[copy.offset : copy.offset + copy.size]
        copy_value = _decode_ascii(copy_raw, copy.padding_byte)
        sources.append(
            FieldSource(
                name=copy.name,
                offset=copy.offset,
                size=copy.size,
                raw_hex=copy_raw.hex().upper(),
                decoded_value=copy_value,
                required_copy=True,
            )
        )
        if copy_value != value:
            consistent = False
            warnings.append(
                f"{field.name} structured value and {copy.name} disagree"
            )
    return (
        DecodedConfigField(
            name=field.name,
            value=value,
            confidence=field.confidence,
            writable=field.writable and consistent,
            consistent=consistent,
            sources=tuple(sources),
        ),
        tuple(warnings),
    )


def inspect_config(
    image: str | Path | DiskImage,
    profiles: Sequence[SystemLayoutProfile] = KNOWN_SYSTEM_PROFILES,
) -> ConfigInspection:
    disk = image if isinstance(image, DiskImage) else DiskImage(image)
    disk.validate_size()
    system = disk.system_area()
    digest = sha256(system).hexdigest()
    candidates = _layout_candidates(system)
    profile = next((item for item in profiles if item.recognizer(system)), None)
    if profile is None:
        partial = any(item.partial_recognizer(system) for item in profiles)
        status: LayoutStatus = "partially recognized" if partial else "unknown"
        return ConfigInspection(
            path=str(disk.path),
            layout_status=status,
            profile_name=None,
            known_hash_match=False,
            system_area_sha256=digest,
            fields=MappingProxyType({}),
            boot_drive_configuration=(
                constants.SYSTEM_CONFIGURATION_TEXT
                if constants.SYSTEM_CONFIGURATION_TEXT.encode("ascii") in system
                else None
            ),
            layout_candidates=candidates,
            warnings=(
                "no supported configuration profile passed structural validation",
                "CAPSLOCK, printer timeout, and autostart require single-setting comparison images",
            ),
        )

    decoded: dict[str, DecodedConfigField] = {}
    warnings: list[str] = []
    for name, field in profile.fields.items():
        value, field_warnings = _decode_field(system, field)
        decoded[name] = value
        warnings.extend(field_warnings)
    for unsupported_name in ("capslock", "printer_timeout", "autostart"):
        decoded.setdefault(unsupported_name, _unknown_field(unsupported_name))
    boot = decoded.get("boot_drive_configuration")
    return ConfigInspection(
        path=str(disk.path),
        layout_status="recognized",
        profile_name=profile.name,
        known_hash_match=digest in profile.known_system_hashes,
        system_area_sha256=digest,
        fields=MappingProxyType(decoded),
        boot_drive_configuration=(
            str(boot.value) if boot is not None and boot.value is not None else None
        ),
        layout_candidates=candidates,
        warnings=tuple(warnings)
        + (
            "CAPSLOCK storage is not confirmed; compare off/on CONFIG captures",
            "printer-timeout storage is not confirmed; compare 20/21/24-second captures",
            "autostart field and empty representation are confirmed; multi-command separators remain unknown",
        ),
    )


def effective_printer_timeout(requested: int) -> int:
    if not 1 <= requested <= 1_024:
        raise ConfigValueError("printer timeout must be between 1 and 1024 seconds")
    return ((requested + 3) // 4) * 4


def _printable_ascii(value: str, field_name: str) -> bytes:
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ConfigValueError(f"{field_name} must contain printable ASCII only") from exc
    if any(byte < 0x20 or byte > 0x7E for byte in encoded):
        raise ConfigValueError(f"{field_name} must not contain control characters")
    return encoded


def _require_editable(
    profile: SystemLayoutProfile,
    inspection: ConfigInspection,
    field_name: str,
) -> tuple[ConfigField, DecodedConfigField]:
    field = profile.fields.get(field_name)
    decoded = inspection.fields.get(field_name)
    if field is None or decoded is None or not field.writable:
        raise UnsupportedConfigEditError(
            f"{field_name} is unsupported for system layout {profile.name}"
        )
    if not decoded.consistent:
        raise ConfigConsistencyError(
            f"cannot edit {field_name}: its required representations are inconsistent"
        )
    return field, decoded


def _string_patches(
    system: bytes,
    field: ConfigField,
    decoded: DecodedConfigField,
    new_value: str,
    *,
    clear: bool,
) -> tuple[ConfigPatch, ...]:
    if clear and not field.clear_supported:
        raise UnsupportedConfigEditError(
            f"clearing {field.name} is unsupported for this system layout"
        )
    encoded = _printable_ascii(new_value, field.name)
    capacity = field.capacity if field.capacity is not None else field.size
    if len(encoded) > capacity:
        raise ConfigValueError(
            f"{field.name} is too long: maximum proven capacity is {capacity} bytes"
        )
    if field.encoding == "length-prefixed-ascii" and field.length_offset is None:
        raise ConfigError(f"profile field {field.name} has no length offset")
    current_length = (
        system[field.length_offset] if field.length_offset is not None else field.size
    )
    if not field.allow_length_change and len(encoded) != current_length:
        raise UnsupportedConfigEditError(
            f"{field.name} length changes are unsupported for this system layout; "
            f"the value must remain exactly {current_length} bytes"
        )
    patches: list[ConfigPatch] = []
    if field.allow_length_change:
        if field.length_offset is not None:
            patches.append(
                ConfigPatch(
                    field_name=f"{field.name}_length",
                    offset=field.length_offset,
                    old_bytes=system[field.length_offset : field.length_offset + 1],
                    new_bytes=bytes([len(encoded)]),
                    current_value=current_length,
                    new_value=len(encoded),
                    reason=f"length byte for structured {field.name} field",
                )
            )
        primary_new = encoded + bytes([field.padding_byte]) * (field.size - len(encoded))
        primary_size = field.size
    else:
        primary_new = encoded
        primary_size = len(encoded)
    patches.append(
        ConfigPatch(
            field_name=field.name,
            offset=field.offset,
            old_bytes=system[field.offset : field.offset + primary_size],
            new_bytes=primary_new,
            current_value=decoded.value,
            new_value=new_value,
            reason=f"structured CONFIG {field.name} field",
        )
    )
    for copy in field.copies:
        if len(encoded) > copy.size:
            raise ConfigValueError(
                f"{field.name} exceeds synchronized copy capacity {copy.size}"
            )
        if not field.allow_length_change and len(encoded) != copy.size:
            raise UnsupportedConfigEditError(
                f"{field.name} must remain exactly {copy.size} bytes to preserve {copy.name}"
            )
        copy_new = encoded + bytes([copy.padding_byte]) * (copy.size - len(encoded))
        patches.append(
            ConfigPatch(
                field_name=copy.name,
                offset=copy.offset,
                old_bytes=system[copy.offset : copy.offset + copy.size],
                new_bytes=copy_new,
                current_value=decoded.value,
                new_value=new_value,
                reason=f"required synchronized generated representation of {field.name}",
            )
        )
    return tuple(patches)


def plan_config_updates(
    image: str | Path | DiskImage,
    updates: ConfigUpdates,
    profiles: Sequence[SystemLayoutProfile] = KNOWN_SYSTEM_PROFILES,
) -> tuple[ConfigInspection, ConfigPatchPlan]:
    if not updates.has_changes:
        raise ConfigValueError("at least one configuration setting must be supplied")
    if updates.autostart is not None and updates.clear_autostart:
        raise ConfigValueError("--autostart and --clear-autostart are mutually exclusive")
    if updates.welcome is not None and updates.clear_welcome:
        raise ConfigValueError("--welcome and --clear-welcome are mutually exclusive")
    disk = image if isinstance(image, DiskImage) else DiskImage(image)
    require_valid_image(disk.path)
    inspection = inspect_config(disk, profiles)
    if inspection.layout_status != "recognized" or inspection.profile_name is None:
        raise UnknownSystemLayoutError(
            f"configuration layout is {inspection.layout_status}; editing is refused"
        )
    profile = next(item for item in profiles if item.name == inspection.profile_name)
    system = disk.system_area()
    patches: list[ConfigPatch] = []
    warnings: list[str] = []
    requested_timeout: int | None = None
    effective_timeout: int | None = None

    if updates.capslock is not None:
        field, decoded = _require_editable(profile, inspection, "capslock")
        if field.encoding != "bitmask-flag" or field.bit_mask is None:
            raise ConfigError("CAPSLOCK field profile is malformed")
        selected = field.enabled_value if updates.capslock else field.disabled_value
        if selected is None:
            raise ConfigError("CAPSLOCK field lacks accepted values")
        old = system[field.offset]
        new = (old & ~field.bit_mask) | selected
        patches.append(
            ConfigPatch(
                "capslock",
                field.offset,
                bytes([old]),
                bytes([new]),
                decoded.value,
                updates.capslock,
                "validated CAPSLOCK bitmask field; unrelated bits preserved",
            )
        )

    if updates.printer_timeout is not None:
        requested_timeout = updates.printer_timeout
        effective_timeout = effective_printer_timeout(requested_timeout)
        field, decoded = _require_editable(profile, inspection, "printer_timeout")
        if field.encoding != "uint-le-units" or field.unit_seconds != 4:
            raise ConfigError("printer timeout field encoding is not confirmed")
        stored = effective_timeout // field.unit_seconds
        new = stored.to_bytes(field.size, "little")
        patches.append(
            ConfigPatch(
                "printer_timeout",
                field.offset,
                system[field.offset : field.offset + field.size],
                new,
                decoded.value,
                effective_timeout,
                "confirmed little-endian count in four-second units",
            )
        )

    if updates.autostart is not None or updates.clear_autostart:
        field, decoded = _require_editable(profile, inspection, "autostart")
        new_value = "" if updates.clear_autostart else updates.autostart or ""
        encoded = _printable_ascii(new_value, "autostart")
        for separator in (";", "|"):
            if separator in new_value and separator not in field.allowed_command_separators:
                raise ConfigValueError(
                    f"autostart separator {separator!r} is unsupported by this layout"
                )
        if encoded:
            warnings.append(
                "Autostart commands run automatically during IPL and may bypass the CP/M prompt."
            )
        patches.extend(
            _string_patches(
                system,
                field,
                decoded,
                new_value,
                clear=updates.clear_autostart,
            )
        )

    if updates.welcome is not None or updates.clear_welcome:
        field, decoded = _require_editable(profile, inspection, "welcome_message")
        new_value = "" if updates.clear_welcome else updates.welcome or ""
        patches.extend(
            _string_patches(
                system,
                field,
                decoded,
                new_value,
                clear=updates.clear_welcome,
            )
        )

    return inspection, ConfigPatchPlan(
        source=str(disk.path),
        profile_name=profile.name,
        patches=tuple(patches),
        requested_printer_timeout=requested_timeout,
        effective_printer_timeout=effective_timeout,
        warnings=tuple(warnings),
    )


def _destination_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _confirm_plan_decodes(
    inspection: ConfigInspection, plan: ConfigPatchPlan
) -> None:
    requested: dict[str, str | int | bool | None] = {}
    for patch in plan.patches:
        if patch.field_name.endswith("_length") or "display_copy" in patch.field_name:
            continue
        requested[patch.field_name] = patch.new_value
    for name, expected in requested.items():
        decoded = inspection.fields.get(name)
        if decoded is None or decoded.value != expected or not decoded.consistent:
            raise ConfigConsistencyError(
                f"post-write decoding of {name} did not reproduce the requested value"
            )


def apply_config_updates(
    image: str | Path,
    updates: ConfigUpdates,
    output: str | Path | None = None,
    *,
    overwrite: bool = True,
    dry_run: bool = False,
    profiles: Sequence[SystemLayoutProfile] = KNOWN_SYSTEM_PROFILES,
) -> tuple[ConfigInspection, ConfigPatchPlan, Path | None]:
    source = Path(image)
    requested_destination = Path(output) if output is not None else source
    inspection, plan = plan_config_updates(source, updates, profiles)
    if dry_run:
        return inspection, plan, None
    in_place = source.resolve(strict=True) == requested_destination.resolve(strict=False)
    destination = source.resolve(strict=True) if in_place else requested_destination
    if _destination_exists(destination) and not overwrite:
        raise FileExistsError(f"output file already exists: {destination}")
    if not destination.parent.is_dir():
        raise ConfigError(f"output directory does not exist: {destination.parent}")
    source_data = DiskImage(source).read_range(0, constants.IMAGE_SIZE)
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary = Path(temporary_name)
        with source.open("rb") as source_stream, os.fdopen(descriptor, "wb") as target:
            shutil.copyfileobj(source_stream, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        with temporary.open("r+b") as stream:
            for patch in plan.patches:
                stream.seek(patch.offset)
                current = stream.read(len(patch.old_bytes))
                if current != patch.old_bytes:
                    raise ConfigConsistencyError(
                        f"expected bytes changed before patching {patch.field_name}"
                    )
                stream.seek(patch.offset)
                stream.write(patch.new_bytes)
            stream.flush()
            os.fsync(stream.fileno())

        require_valid_image(temporary)
        result_inspection = inspect_config(temporary, profiles)
        if result_inspection.profile_name != plan.profile_name:
            raise ConfigConsistencyError("configuration profile was not recognized after editing")
        _confirm_plan_decodes(result_inspection, plan)
        result_data = DiskImage(temporary).read_range(0, constants.IMAGE_SIZE)
        allowed_offsets = {
            offset
            for patch in plan.patches
            for offset in range(patch.offset, patch.offset + len(patch.old_bytes))
        }
        unexpected = next(
            (
                offset
                for offset, (old, new) in enumerate(zip(source_data, result_data, strict=True))
                if old != new and offset not in allowed_offsets
            ),
            None,
        )
        if unexpected is not None:
            raise ConfigConsistencyError(
                f"configuration update changed unplanned byte offset {unexpected}"
            )
        if result_data[constants.SYSTEM_AREA_SIZE :] != source_data[constants.SYSTEM_AREA_SIZE :]:
            raise ConfigConsistencyError("bytes after LBA 31 changed during configuration update")
        if _destination_exists(destination) and not overwrite:
            raise FileExistsError(f"output file already exists: {destination}")
        os.replace(temporary, destination)
        temporary = None
        return inspection, plan, requested_destination
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
