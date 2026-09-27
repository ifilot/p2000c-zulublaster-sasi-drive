cmake_minimum_required(VERSION 3.16)
project(p2000c_mini LANGUAGES C CXX)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(z80 STATIC src/third_party/superzazu_z80/z80.c)
target_include_directories(z80 PUBLIC src/third_party/superzazu_z80)
add_library(i8088 STATIC src/third_party/blink16_8086/i8088.cpp)
target_include_directories(i8088 PUBLIC src/third_party/blink16_8086)
add_executable(p2000c-mini
  src/main.cpp
  src/core/p2000c_machine.cpp
  src/core/copower_board.cpp
  src/core/raw_disk_image.cpp
  src/core/terminal.cpp
)
target_include_directories(p2000c-mini PRIVATE src)
target_link_libraries(p2000c-mini PRIVATE z80 i8088)

if(EMSCRIPTEN)
  add_executable(p2000c-web
    src/web_main.cpp
    src/core/p2000c_machine.cpp
    src/core/copower_board.cpp
    src/core/raw_disk_image.cpp
    src/core/terminal.cpp
  )
  target_include_directories(p2000c-web PRIVATE src)
  target_link_libraries(p2000c-web PRIVATE z80 i8088)
  set_target_properties(p2000c-web PROPERTIES SUFFIX ".js")
  target_link_options(p2000c-web PRIVATE
    "-sMODULARIZE=1"
    "-sEXPORT_NAME=createP2000C"
    "-sALLOW_MEMORY_GROWTH=1"
    "-sINITIAL_MEMORY=50331648"
    "-sENVIRONMENT=web,worker,node"
    "-sFILESYSTEM=1"
    "-sEXPORTED_RUNTIME_METHODS=['FS','UTF8ToString']"
    "-sNO_EXIT_RUNTIME=1"
    "--no-entry"
  )
endif()
