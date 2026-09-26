#ifndef P2000C_CORE_RAW_DISK_IMAGE_H_
#define P2000C_CORE_RAW_DISK_IMAGE_H_

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace p2000c {

/** A directly writable P2000C raw disk image with size-inferred geometry. */
class RawDiskImage {
 public:
  enum class Kind {
    kFloppy,
    kHardDisk,
  };

  /** Physical SASI block size and legacy CP/M floppy sector size. */
  static constexpr std::size_t kSectorSize = 256;
  static constexpr std::size_t kFloppyCylinders = 80;
  static constexpr std::size_t kFloppyHeads = 2;
  static constexpr std::size_t kFloppySectorsPerTrack = 16;
  static constexpr std::size_t kFloppySize = 640 * 1024;
  static constexpr std::size_t kDosFloppySectorsPerTrack = 10;
  static constexpr std::size_t kDosFloppySectorSize = 512;
  static constexpr std::size_t kDosFloppySize = 800 * 1024;
  static constexpr std::size_t kHardDiskSize = 10 * 1024 * 1024;
  static_assert(kFloppySize == kFloppyCylinders * kFloppyHeads *
                                    kFloppySectorsPerTrack * kSectorSize);
  static_assert(kDosFloppySize ==
                kFloppyCylinders * kFloppyHeads *
                    kDosFloppySectorsPerTrack * kDosFloppySectorSize);

  /** Opens an image and verifies one of the supported exact sizes. */
  static std::optional<RawDiskImage> open(const std::filesystem::path& path,
                                          Kind kind, std::string* error);

  /** Returns the mounted image kind. */
  Kind kind() const { return kind_; }

  /** Returns the mounted file path. */
  const std::filesystem::path& path() const { return path_; }

  /** Returns the complete raw byte sequence. */
  std::span<const std::uint8_t> data() const { return data_; }

  /** Returns the physical sector byte size of a mounted floppy. */
  std::size_t floppy_sector_size() const { return floppy_sector_size_; }

  /** Returns the physical sector count per floppy track. */
  std::size_t floppy_sectors_per_track() const {
    return floppy_sectors_per_track_;
  }

  /** Returns one floppy sector in cylinder/head/sector order. */
  std::span<const std::uint8_t> floppy_sector(
      std::uint8_t cylinder, std::uint8_t head,
      std::uint8_t sector) const;

  /** Returns a contiguous sequence of 256-byte logical blocks. */
  std::span<const std::uint8_t> blocks(std::size_t lba,
                                       std::size_t count) const;

  /** Writes one floppy sector through to the mounted file. */
  bool write_floppy_sector(std::uint8_t cylinder, std::uint8_t head,
                           std::uint8_t sector,
                           std::span<const std::uint8_t> data,
                           std::string* error);

  /** Writes contiguous 256-byte logical blocks through to the file. */
  bool write_blocks(std::size_t lba, std::span<const std::uint8_t> data,
                    std::string* error);

 private:
  /** Returns a raw floppy-sector byte offset, or no value when invalid. */
  std::optional<std::size_t> floppy_offset(
      std::uint8_t cylinder, std::uint8_t head,
      std::uint8_t sector) const;

  /** Replaces a checked byte range in memory and on disk. */
  bool write(std::size_t offset, std::span<const std::uint8_t> data,
             std::string* error);

  std::filesystem::path path_;
  Kind kind_ = Kind::kFloppy;
  std::vector<std::uint8_t> data_;
  std::size_t floppy_sector_size_ = kSectorSize;
  std::size_t floppy_sectors_per_track_ = kFloppySectorsPerTrack;
};

}  // namespace p2000c

#endif  // P2000C_CORE_RAW_DISK_IMAGE_H_
