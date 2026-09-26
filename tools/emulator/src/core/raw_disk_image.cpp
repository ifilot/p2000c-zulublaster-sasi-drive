#include "core/raw_disk_image.h"

#include <algorithm>
#include <fstream>
#include <iterator>
#include <utility>

namespace p2000c {
namespace {

void set_error(std::string* error, std::string message) {
  if (error != nullptr) {
    *error = std::move(message);
  }
}

const char* kind_name(RawDiskImage::Kind kind) {
  return kind == RawDiskImage::Kind::kFloppy ? "FLP floppy" : "HDA hard disk";
}

}  // namespace

std::optional<RawDiskImage> RawDiskImage::open(
    const std::filesystem::path& path, Kind kind, std::string* error) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    set_error(error, "Could not open raw disk image: " + path.string());
    return std::nullopt;
  }

  RawDiskImage image;
  image.path_ = path;
  image.kind_ = kind;
  image.data_.assign(std::istreambuf_iterator<char>(input),
                     std::istreambuf_iterator<char>());
  bool valid_size = false;
  if (kind == Kind::kFloppy) {
    if (image.data_.size() == kFloppySize) {
      valid_size = true;
    } else if (image.data_.size() == kDosFloppySize) {
      image.floppy_sector_size_ = kDosFloppySectorSize;
      image.floppy_sectors_per_track_ = kDosFloppySectorsPerTrack;
      valid_size = true;
    }
  } else {
    valid_size = image.data_.size() == kHardDiskSize;
  }
  if (!valid_size) {
    const std::string expected =
        kind == Kind::kFloppy
            ? std::to_string(kFloppySize) + " or " +
                  std::to_string(kDosFloppySize)
            : std::to_string(kHardDiskSize);
    set_error(error, std::string("A raw ") + kind_name(kind) +
                         " image must be exactly " + expected +
                         " bytes; got " +
                         std::to_string(image.data_.size()) + ".");
    return std::nullopt;
  }
  return image;
}

std::optional<std::size_t> RawDiskImage::floppy_offset(
    std::uint8_t cylinder, std::uint8_t head, std::uint8_t sector) const {
  if (cylinder >= kFloppyCylinders || head >= kFloppyHeads || sector == 0 ||
      sector > floppy_sectors_per_track_) {
    return std::nullopt;
  }
  const std::size_t logical_sector =
      (static_cast<std::size_t>(cylinder) * kFloppyHeads + head) *
          floppy_sectors_per_track_ +
      sector - 1;
  return logical_sector * floppy_sector_size_;
}

std::span<const std::uint8_t> RawDiskImage::floppy_sector(
    std::uint8_t cylinder, std::uint8_t head, std::uint8_t sector) const {
  if (kind_ != Kind::kFloppy) {
    return {};
  }
  const std::optional<std::size_t> offset =
      floppy_offset(cylinder, head, sector);
  if (!offset.has_value()) {
    return {};
  }
  return std::span<const std::uint8_t>(data_).subspan(
      *offset, floppy_sector_size_);
}

std::span<const std::uint8_t> RawDiskImage::blocks(
    std::size_t lba, std::size_t count) const {
  if (lba > data_.size() / kSectorSize ||
      count > data_.size() / kSectorSize - lba) {
    return {};
  }
  return std::span<const std::uint8_t>(data_).subspan(
      lba * kSectorSize, count * kSectorSize);
}

bool RawDiskImage::write_floppy_sector(
    std::uint8_t cylinder, std::uint8_t head, std::uint8_t sector,
    std::span<const std::uint8_t> data, std::string* error) {
  const std::optional<std::size_t> offset =
      kind_ == Kind::kFloppy ? floppy_offset(cylinder, head, sector)
                             : std::nullopt;
  if (!offset.has_value() || data.size() != floppy_sector_size_) {
    set_error(error, "Invalid raw floppy sector write.");
    return false;
  }
  return write(*offset, data, error);
}

bool RawDiskImage::write_blocks(std::size_t lba,
                                std::span<const std::uint8_t> data,
                                std::string* error) {
  if (data.size() % kSectorSize != 0 ||
      lba > data_.size() / kSectorSize ||
      data.size() / kSectorSize > data_.size() / kSectorSize - lba) {
    set_error(error, "Invalid raw disk block write.");
    return false;
  }
  return write(lba * kSectorSize, data, error);
}

bool RawDiskImage::write(std::size_t offset,
                         std::span<const std::uint8_t> data,
                         std::string* error) {
  if (offset > data_.size() || data.size() > data_.size() - offset) {
    set_error(error, "Raw disk write lies outside the image.");
    return false;
  }
  std::fstream output(path_, std::ios::binary | std::ios::in | std::ios::out);
  if (!output) {
    set_error(error, "Could not open raw disk image for writing: " +
                         path_.string());
    return false;
  }
  output.seekp(static_cast<std::streamoff>(offset));
  output.write(reinterpret_cast<const char*>(data.data()),
               static_cast<std::streamsize>(data.size()));
  output.flush();
  if (!output) {
    set_error(error, "Failed while writing raw disk image: " + path_.string());
    return false;
  }
  std::copy(data.begin(), data.end(), data_.begin() + offset);
  return true;
}

}  // namespace p2000c
