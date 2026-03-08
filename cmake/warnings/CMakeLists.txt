# cmake-format: off
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2019 by The qTox Project Contributors
# Copyright © 2024-2025 The TokTok team
# cmake-format: on

project(qtox_warnings)

add_library(${PROJECT_NAME} INTERFACE)
add_library(qtox::warnings ALIAS ${PROJECT_NAME})

if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
  if("${CMAKE_CXX_COMPILER_FRONTEND_VARIANT}" STREQUAL "MSVC")
    set(CLANGCL ON)
  else()
    set(CLANG ON)
  endif()
endif()

include(CheckCXXCompilerFlag)

# Conversion / type-safety
check_cxx_compiler_flag(-Wconversion             COMPILER_SUPPORTS_WCONVERSION)
check_cxx_compiler_flag(-Wsign-conversion        COMPILER_SUPPORTS_WSIGN_CONVERSION)
check_cxx_compiler_flag(-Wimplicit-fallthrough   COMPILER_SUPPORTS_WIMPLICIT_FALLTHROUGH)
check_cxx_compiler_flag(-Wcast-qual             COMPILER_SUPPORTS_WCAST_QUAL)
check_cxx_compiler_flag(-Walloca               COMPILER_SUPPORTS_WALLOCA)
check_cxx_compiler_flag(-Wvla                  COMPILER_SUPPORTS_WVLA)
check_cxx_compiler_flag(-Wstrict-aliasing=2    COMPILER_SUPPORTS_WSTRICT_ALIASING)
check_cxx_compiler_flag(-Wzero-as-null-pointer-constant COMPILER_SUPPORTS_WNULL_PTR)

# GCC-specific overflow / bounds checks
check_cxx_compiler_flag(-Wformat-overflow=2    COMPILER_SUPPORTS_WFORMAT_OVERFLOW)
check_cxx_compiler_flag(-Wformat-truncation=2  COMPILER_SUPPORTS_WFORMAT_TRUNCATION)
check_cxx_compiler_flag(-Warray-bounds=2       COMPILER_SUPPORTS_WARRAY_BOUNDS)
check_cxx_compiler_flag(-Wshift-overflow=2     COMPILER_SUPPORTS_WSHIFT_OVERFLOW)
check_cxx_compiler_flag(-Wstringop-overflow=4  COMPILER_SUPPORTS_WSTRINGOP_OVERFLOW)
check_cxx_compiler_flag(-Wstringop-truncation  COMPILER_SUPPORTS_WSTRINGOP_TRUNCATION)
check_cxx_compiler_flag(-Winit-self            COMPILER_SUPPORTS_WINIT_SELF)

# Clang-specific
check_cxx_compiler_flag(-Wthread-safety               COMPILER_SUPPORTS_WTHREAD_SAFETY)
check_cxx_compiler_flag(-Wdeprecated-copy-dtor        COMPILER_SUPPORTS_WDEPRECATED_COPY_DTOR)

target_compile_options(
  ${PROJECT_NAME}
  INTERFACE
    $<$<OR:$<BOOL:${CLANG}>,$<CXX_COMPILER_ID:GNU>>:
    -fno-common;
    -fstrict-overflow;
    -ftrapv;
    -pedantic-errors;
    -Wall;
    -Wcast-align;
    -Wdouble-promotion;
    -Wextra;
    -Wformat=2;
    -Wnon-virtual-dtor;
    -Wnull-dereference;
    -Wold-style-cast;
    -Woverloaded-virtual;
    -Wshadow;
    -Wsign-compare;
    -Wundef;
    -Wuninitialized;
    >
    $<$<CXX_COMPILER_ID:GNU>:
    -Wduplicated-cond;
    -Wlogical-op;
    >
    $<$<BOOL:${CLANG}>:
    -Wno-gnu-zero-variadic-macro-arguments; # Required for gtest 1.10.
    >
    $<$<OR:$<BOOL:${CLANGCL}>,$<CXX_COMPILER_ID:MSVC>>:
    /permissive-;
    /W4;
    /w14254; # 'operator': conversion from 'type1:field_bits' to
             # 'type2:field_bits', possible loss of data
    /w14263; # 'function': member function does not override any base class
             # virtual member function
    /w14265; # 'classname': class has virtual functions, but destructor is not
             # virtual instances of this class may not be destructed correctly
    /w14287; # 'operator': unsigned/negative constant mismatch
    /w14289; # nonstandard extension used: 'variable': loop control variable
             # declared in the for-loop is used outside the for-loop scope
    /w14296; # 'operator': expression is always 'boolean_value'
    /w14311; # 'variable': pointer truncation from 'type1' to 'type2'
    /w14545; # expression before comma evaluates to a function which is missing
             # an argument list
    /w14546; # function call before comma missing argument list
    /w14547; # 'operator': operator before comma has no effect; expected
             # operator with side-effect
    /w14549; # 'operator': operator before comma has no effect; did you intend
             # 'operator'?
    /w14555; # expression has no effect; expected expression with side- effect
    /w14619; # pragma warning: there is no warning number 'number'
    /w14640; # Enable warning on thread un-safe static member initialization
    /w14826; # Conversion from 'type1' to 'type_2' is sign-extended. This may
             # cause unexpected runtime behavior.
    /w14928; # illegal copy-initialization; more than one user-defined
             # conversion has been implicitly applied
    /wd4244; # 'argument': conversion from 'int' to 'unsigned char', possible
             # loss of data # This one is sort of required for gtest.
    /WX;
    >
    $<$<BOOL:${STRICT_OPTIONS}>:
    -Werror;
    >
    $<$<AND:$<NOT:$<BOOL:${WIN32}>>,$<NOT:$<BOOL:${HAIKU}>>>:
    -Wstack-protector;
    >
    # Conversion / type-safety
    $<$<BOOL:${COMPILER_SUPPORTS_WCONVERSION}>:         -Wconversion;>
    $<$<BOOL:${COMPILER_SUPPORTS_WSIGN_CONVERSION}>:    -Wsign-conversion;>
    $<$<BOOL:${COMPILER_SUPPORTS_WIMPLICIT_FALLTHROUGH}>:-Wimplicit-fallthrough;>
    $<$<BOOL:${COMPILER_SUPPORTS_WCAST_QUAL}>:          -Wcast-qual;>
    $<$<BOOL:${COMPILER_SUPPORTS_WNULL_PTR}>:           -Wzero-as-null-pointer-constant;>
    $<$<BOOL:${COMPILER_SUPPORTS_WSTRICT_ALIASING}>:    -Wstrict-aliasing=2;>
    # Dangerous constructs
    $<$<BOOL:${COMPILER_SUPPORTS_WALLOCA}>:             -Walloca;>
    $<$<BOOL:${COMPILER_SUPPORTS_WVLA}>:                -Wvla;>
    # GCC-specific overflow / bounds checks
    $<$<BOOL:${COMPILER_SUPPORTS_WFORMAT_OVERFLOW}>:    -Wformat-overflow=2;>
    $<$<BOOL:${COMPILER_SUPPORTS_WFORMAT_TRUNCATION}>:  -Wformat-truncation=2;>
    $<$<BOOL:${COMPILER_SUPPORTS_WARRAY_BOUNDS}>:       -Warray-bounds=2;>
    $<$<BOOL:${COMPILER_SUPPORTS_WSHIFT_OVERFLOW}>:     -Wshift-overflow=2;>
    $<$<BOOL:${COMPILER_SUPPORTS_WSTRINGOP_OVERFLOW}>:  -Wstringop-overflow=4;>
    $<$<BOOL:${COMPILER_SUPPORTS_WSTRINGOP_TRUNCATION}>:-Wstringop-truncation;>
    $<$<BOOL:${COMPILER_SUPPORTS_WINIT_SELF}>:          -Winit-self;>
    # Clang-specific
    $<$<BOOL:${COMPILER_SUPPORTS_WTHREAD_SAFETY}>:      -Wthread-safety;>
    $<$<BOOL:${COMPILER_SUPPORTS_WDEPRECATED_COPY_DTOR}>:-Wdeprecated-copy-dtor;>)
