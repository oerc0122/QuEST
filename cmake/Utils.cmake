find_package(Git REQUIRED)

include(ExternalProject)

macro(PythonMod utilName GitRepo)
  if (${ARGC} LESS 2)
    message(FATAL_ERROR "PythonMod requires util name and git repo to be supplied.")
  endif()
  if (${ARGC} GREATER 2)
    message(WARNING "PythonMod requires only util name and git repo to be supplied, extra arguments will be ignored.")
  endif()
  ExternalProject_Add(
      ${utilName}
      GIT_REPOSITORY "${GitRepo}"
      PREFIX ${PROJECT_SOURCE_DIR}/Utilities/${utilName}
      BINARY_DIR ${PROJECT_SOURCE_DIR}/Utilities/${utilName}
      UPDATE_COMMAND ${GIT_EXECUTABLE} pull
      BUILD_COMMAND ${CMAKE_COMMAND} -E copy_directory <SOURCE_DIR> <BINARY_DIR>
      BUILD_ALWAYS OFF
      EXCLUDE_FROM_ALL ON
      CONFIGURE_COMMAND ""
      TEST_COMMAND ""
      INSTALL_COMMAND ""
      GIT_SUBMODULES ""
  )
endmacro()

PythonMod (QuESTPy git@github.com:oerc0122/QuESTPy.git)
PythonMod (QuESTTest git@github.com:oerc0122/QuESTTest.git)
add_dependencies(QuESTTest QuESTPy)
PythonMod (pyquest-cffi https://github.com/HQSquantumsimulations/pyquest.git)
