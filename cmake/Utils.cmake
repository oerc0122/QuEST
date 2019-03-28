find_package(Git REQUIRED)
set(Python_ADDITIONAL_VERSIONS 3.4;3.5;3.6;3.7;3.8)
find_package(PythonInterp)

include(ExternalProject)

if (LOCAL_UTILS)
  set (UTIL_ROOT "${PROJECT_BINARY_DIR}/Utilities/" CACHE STRING "Path to Utilities")
else()
  set (UTIL_ROOT "${PROJECT_SOURCE_DIR}/Utilities/" CACHE STRING "Path to Utilities")
endif()

macro(PythonMod utilName GitRepo)
  if (PYTHONINTERP_FOUND)
    
    if (${ARGC} LESS 2)
      message(FATAL_ERROR "PythonMod requires util name and git repo to be supplied.")
    endif()
    if (${ARGC} GREATER 2)
      message(WARNING "PythonMod requires only util name and git repo to be supplied, extra arguments will be ignored.")
    endif()
    set(${utilName}_PATH ${UTIL_ROOT}${utilName} CACHE PATH "Path to ${utilName}")
    ExternalProject_Add(
      ${utilName}
      GIT_REPOSITORY "${GitRepo}"
      PREFIX ${${utilName}_PATH}
      BINARY_DIR ${${utilName}_PATH}
      UPDATE_COMMAND ${GIT_EXECUTABLE} pull
      BUILD_COMMAND ${CMAKE_COMMAND} -E copy_directory <SOURCE_DIR> <BINARY_DIR>
      BUILD_ALWAYS OFF
      EXCLUDE_FROM_ALL ON
      CONFIGURE_COMMAND ""
      TEST_COMMAND ""
      INSTALL_COMMAND ""
      GIT_SUBMODULES ""
      )
  else()
    message(WARNING "Python not found on system -- Disabling ${utilName}")
  endif()
endmacro()

PythonMod (QuESTPy git@github.com:oerc0122/QuESTPy.git)
if (QuESTPy)
  add_dependencies(QuESTPy QuEST)
  add_custom_target( update_QuEST_lib_loc
    DEPENDS QuESTPy
    DEPENDS QuEST
    COMMAND ${CMAKE_COMMAND} -DQuEST_ROOT=${PROJECT_SOURCE_DIR} -DQuESTPy_PATH=${QuESTPy_PATH} -DQuEST_LIB_EXACT=${QuEST_LIB_EXACT} -DQuEST_LIB_PATH=${QuEST_LIB_PATH} -P ${PROJECT_SOURCE_DIR}/cmake/QuESTPyLib.cmake
    )
endif()

PythonMod (QuESTTest git@github.com:oerc0122/QuESTTest.git)
if (QuESTTest)
  add_dependencies(QuESTTest QuEST QuESTPy)
endif()

PythonMod (pyquest-cffi https://github.com/HQSquantumsimulations/pyquest.git)
if (pyquest-cffi)
  add_dependencies(pyquest-cffi QuEST)
endif()
