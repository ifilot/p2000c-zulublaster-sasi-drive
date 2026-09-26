"""Tools for Philips P2000C CP/M hard-drive images."""

from .allocation import AllocationAnalysisReport, analyze_allocation
from .builder import build_image
from .config import (
    ConfigInspection,
    ConfigPatchPlan,
    ConfigUpdates,
    apply_config_updates,
    effective_printer_timeout,
    inspect_config,
    plan_config_updates,
)
from .directory import DirectoryEntry, read_directory
from .filesystem import (
    CPMFile,
    delete_file,
    extract_file,
    list_files,
    normalize_cpm_filename,
    put_file,
    put_files,
    read_file,
)
from .image import DiskImage, ImageFormatError, SectorRange
from .verify import VerificationReport, verify_image
from .system_compare import (
    SystemComparisonReport,
    compare_system_areas,
    compare_system_images,
)

__all__ = [
    "DirectoryEntry",
    "DiskImage",
    "ImageFormatError",
    "SectorRange",
    "AllocationAnalysisReport",
    "analyze_allocation",
    "ConfigInspection",
    "ConfigPatchPlan",
    "ConfigUpdates",
    "SystemComparisonReport",
    "apply_config_updates",
    "compare_system_images",
    "compare_system_areas",
    "effective_printer_timeout",
    "inspect_config",
    "CPMFile",
    "VerificationReport",
    "build_image",
    "delete_file",
    "extract_file",
    "list_files",
    "normalize_cpm_filename",
    "plan_config_updates",
    "put_file",
    "put_files",
    "read_file",
    "read_directory",
    "verify_image",
]

from .version import VERSION as __version__
