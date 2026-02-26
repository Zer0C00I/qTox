# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2024-2025 The TokTok team

################################################################################
#
# :: clang-tidy static analysis
#
# clang-tidy-check target is always available:
#   cmake --build _build --target clang-tidy-check
#
# To also run clang-tidy on every TU during the normal build:
#   cmake -DCLANG_TIDY=ON ...
#
################################################################################

find_program(CLANG_TIDY_EXE
  NAMES clang-tidy
  DOC "Path to clang-tidy executable")

if(CLANG_TIDY_EXE)
  message(STATUS "clang-tidy: ${CLANG_TIDY_EXE}")
else()
  message(STATUS "clang-tidy: not found (clang-tidy-check target will be unavailable)")
endif()

# Wire clang-tidy into the normal CXX compilation pipeline when CLANG_TIDY=ON.
# Every TU compiled by the project will also be analysed.
if(CLANG_TIDY)
  if(NOT CLANG_TIDY_EXE)
    message(FATAL_ERROR
      "CLANG_TIDY=ON but clang-tidy was not found. "
      "Install clang-tidy or set CLANG_TIDY=OFF.")
  endif()
  set(CMAKE_CXX_CLANG_TIDY
      "${CLANG_TIDY_EXE}"
      "--extra-arg=-std=c++23"
      "--use-color"
      "-p=${CMAKE_BINARY_DIR}"
      CACHE STRING "clang-tidy command" FORCE)
else()
  # Explicitly clear in case a previous configure had CLANG_TIDY=ON.
  set(CMAKE_CXX_CLANG_TIDY "" CACHE STRING "clang-tidy command" FORCE)
endif()

# Standalone target — always registered so it works regardless of CLANG_TIDY.
# Requires clang-tidy to be installed; fails with a clear message if not found.
if(CLANG_TIDY_EXE)
  add_custom_target(clang-tidy-check
    COMMAND
      ${CLANG_TIDY_EXE}
      "--extra-arg=-std=c++23"
      "--use-color"
      "-p=${CMAKE_BINARY_DIR}"
      $<TARGET_PROPERTY:${BINARY_NAME}_static,SOURCES>
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Running clang-tidy on all qtox_static sources"
    VERBATIM)
else()
  add_custom_target(clang-tidy-check
    COMMAND ${CMAKE_COMMAND} -E echo
      "clang-tidy-check: clang-tidy not found. Install clang-tidy and re-run cmake."
    COMMAND ${CMAKE_COMMAND} -E false)
endif()
