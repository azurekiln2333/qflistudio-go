# Build the parser/formatter/debugger used by desktop IDE features. Desktop
# program execution continues to use the installed official Go SDK.
if(WIN32)
  set(QFLI_GO_LIBRARY_NAME "qfli_go_runtime.dll")
else()
  set(QFLI_GO_LIBRARY_NAME "libqfli_go_runtime.so")
endif()
set(QFLI_GO_MODULE "${CMAKE_CURRENT_LIST_DIR}")
set(QFLI_GO_RUNTIME_LIBRARY "${CMAKE_CURRENT_BINARY_DIR}/${QFLI_GO_LIBRARY_NAME}")
set(QFLI_GO_RUNTIME_ARTIFACT "$ENV{QFLI_GO_RUNTIME_ARTIFACT}")

if(NOT "${QFLI_GO_RUNTIME_ARTIFACT}" STREQUAL "")
  if(NOT IS_ABSOLUTE "${QFLI_GO_RUNTIME_ARTIFACT}")
    message(FATAL_ERROR "QFLI_GO_RUNTIME_ARTIFACT must be an absolute path.")
  endif()
  if(NOT EXISTS "${QFLI_GO_RUNTIME_ARTIFACT}" OR IS_DIRECTORY "${QFLI_GO_RUNTIME_ARTIFACT}")
    message(FATAL_ERROR "QFLI_GO_RUNTIME_ARTIFACT does not name an existing library.")
  endif()
  get_filename_component(QFLI_GO_ARTIFACT_NAME "${QFLI_GO_RUNTIME_ARTIFACT}" NAME)
  if(NOT QFLI_GO_ARTIFACT_NAME STREQUAL QFLI_GO_LIBRARY_NAME)
    message(FATAL_ERROR "QFLI_GO_RUNTIME_ARTIFACT has the wrong library name.")
  endif()
  file(SIZE "${QFLI_GO_RUNTIME_ARTIFACT}" QFLI_GO_ARTIFACT_SIZE)
  if(QFLI_GO_ARTIFACT_SIZE LESS 1)
    message(FATAL_ERROR "QFLI_GO_RUNTIME_ARTIFACT is empty.")
  endif()
  add_custom_command(
    OUTPUT "${QFLI_GO_RUNTIME_LIBRARY}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
      "${QFLI_GO_RUNTIME_ARTIFACT}" "${QFLI_GO_RUNTIME_LIBRARY}"
    DEPENDS "${QFLI_GO_RUNTIME_ARTIFACT}"
    COMMENT "Staging the validated source-matched Go IDE runtime"
    VERBATIM)
else()
  set(QFLI_GO_EXECUTABLE "$ENV{QFLI_GO_EXECUTABLE}" CACHE FILEPATH "Local Go executable")
  if(NOT QFLI_GO_EXECUTABLE)
    find_program(QFLI_GO_EXECUTABLE_FOUND NAMES go)
    if(NOT QFLI_GO_EXECUTABLE_FOUND)
      message(FATAL_ERROR "A local Go SDK is required. Set QFLI_GO_EXECUTABLE to its go executable.")
    endif()
    set(QFLI_GO_EXECUTABLE "${QFLI_GO_EXECUTABLE_FOUND}")
  endif()
  set(QFLI_GO_CC "$ENV{QFLI_GO_CC}" CACHE STRING "C compiler for Go cgo")
  if(NOT QFLI_GO_CC)
    find_program(QFLI_GO_CC_FOUND NAMES gcc clang)
    if(NOT QFLI_GO_CC_FOUND)
      message(FATAL_ERROR "A cgo compiler is required. Set QFLI_GO_CC to a compatible gcc/clang command.")
    endif()
    set(QFLI_GO_CC "${QFLI_GO_CC_FOUND}")
  endif()
  file(GLOB_RECURSE QFLI_GO_SOURCE_FILES CONFIGURE_DEPENDS
    "${QFLI_GO_MODULE}/*.go")
  add_custom_command(
    OUTPUT "${QFLI_GO_RUNTIME_LIBRARY}"
    COMMAND "${CMAKE_COMMAND}" -E env
      "CGO_ENABLED=1" "GOTOOLCHAIN=local" "GOWORK=off" "GOENV=off"
      "GOPROXY=off" "GOSUMDB=off"
      "GO_TELEMETRY_CHILD=2"
      "CC=${QFLI_GO_CC}"
      "${QFLI_GO_EXECUTABLE}" build -mod=vendor -buildmode=c-shared
      -o "${QFLI_GO_RUNTIME_LIBRARY}" .
    WORKING_DIRECTORY "${QFLI_GO_MODULE}"
    DEPENDS ${QFLI_GO_SOURCE_FILES} "${QFLI_GO_MODULE}/go.mod"
      "${QFLI_GO_MODULE}/go.sum" "${QFLI_GO_MODULE}/vendor/modules.txt"
    COMMENT "Building the offline Go IDE runtime"
    VERBATIM)
endif()

add_custom_target(qfli_go_runtime_library DEPENDS "${QFLI_GO_RUNTIME_LIBRARY}")
add_dependencies(${BINARY_NAME} qfli_go_runtime_library)
