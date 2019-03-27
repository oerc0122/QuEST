# Calculate possible tests

option(GENERATE_BENCHMARK "Generate set of unit tests for this build" OFF)
option(ENABLE_ADVANCED_TEST "Enable specific unit testing for advanced users" OFF)
set(TEST_NQUBITS 4 CACHE STRING "Number of qubits to run when running tests")
set(TEST_TYPES "PMS" CACHE STRING "Type of tests to generate")
set(TEST_QUREG "ZPDN" CACHE STRING "Types of qureg to generate in tests")
set(TEST_GENERATE "unit" CACHE STRING "Tests to generate on generate benchmarks")

set(TEST_DIR "${QuEST_Project_BINARY_DIR}/CustomTests" CACHE PATH "Testing files output directory")
set(TESTCOMMAND "${CMAKE_CURRENT_SOURCE_DIR}/QuESTTest.py")


add_custom_target("benchmark"
  DEPENDS QuEST
  COMMAND ${CMAKE_COMMAND} -P  ${QuEST_Project_SOURCE_DIR} -DGENERATE_BENCHMARK=ON
  )

if (GENERATE_BENCHMARK)
  message(STATUS "Generating benchmarking test results")
  message(STATUS "${TEST_NQUBITS} Qubits, ${TEST_TYPES}, ${TEST_QUREG}, ${TEST_GENERATE}")
  set(GENERATE_BENCHMARK OFF CACHE BOOL "Generate set of unit tests for this build" FORCE)
  set(BENCHMARKS_EXIST ON CACHE BOOL "Add custom tests to test search dir") 
  execute_process(
    COMMAND mkdir -p ${TEST_DIR}
    COMMAND ${PYTHON_EXECUTABLE} ${TESTCOMMAND} -Q ${QuEST_LIB_PATH} ${INCLUDE_TESTS} -q -n ${TEST_NQUBITS} -T ${TEST_TYPES} -V ${TEST_QUREG} -g ${TEST_GENERATE}
    )
  message(STATUS "Generating benchmarking test results -- DONE") 
endif()
  
if(${ENABLE_ADVANCED_TEST})

  # Get list of test sets
  execute_process(
    DEPENDS QuESTTest
    COMMAND ${TESTCOMMAND} -L
    OUTPUT_VARIABLE AVAILABLE_TESTS
    )
  # Make semi-colon separated list as required by Cmake
  string(REPLACE "\n" "\;" AVAILABLE_TESTS "${AVAILABLE_TESTS}")
  # Cast string into list
  set(AVAILABLE_TESTS ${AVAILABLE_TESTS})

  # Add all tests into available test list
  foreach(TEST ${AVAILABLE_TESTS})
    add_test(
      NAME ${TEST}
      CONFIGURATIONS debug
      COMMAND ${PYTHON_EXECUTABLE} ${TESTCOMMAND} $<BENCHMARKS_EXIST:-p ${TEST_DIR}> -Q ${QuEST_LIB_PATH} ${TEST}
      )
    set_tests_properties(${TEST}
      PROPERTIES
      PASS_REGULAR_EXPRESSION " 0 failed"
      FAIL_REGULAR_EXPRESSION "Error")
    add_custom_target("test_${TEST}"
      DEPENDS QuEST
      COMMAND ctest -R ${TEST}
      )
  endforeach(TEST)

else()

  # Add unit test into tests (Core)
  add_test(unit
    ${PYTHON_EXECUTABLE} ${TESTCOMMAND} $<BENCHMARKS_EXIST:-p ${TEST_DIR}> -Q ${QuEST_LIB_PATH} unit)
  set_tests_properties(unit
    PROPERTIES
    PASS_REGULAR_EXPRESSION " 0 failed"
    FAIL_REGULAR_EXPRESSION "[eE]rror") 
endif()
  


