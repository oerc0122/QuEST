# Calculate possible tests

option(ENABLE_ADVANCED_TEST "Enable specific unit testing for advanced users" OFF)
set(TEST_NQUBITS 4 CACHE STRING "Number of qubits to run when running tests")
set(TEST_TYPES "PMS" CACHE STRING "Type of tests to generate")
set(TEST_QUREG "ZPDN" CACHE STRING "Types of qureg to generate in tests")
set(TEST_GENERATE "unit" CACHE STRING "Tests to generate on generate benchmarks")

set(TEST_DIR "${QuEST_Project_BINARY_DIR}/CustomTests" CACHE PATH "Testing files output directory")
set(TESTCOMMAND ${PYTHON_EXECUTABLE} -m QuESTTest)

add_custom_target("benchmark"
  DEPENDS QuESTTest
  DEPENDS QuEST
  COMMAND mkdir -p ${TEST_DIR}
  COMMAND ${TESTCOMMAND} -Q ${QuEST_LIB_PATH} ${INCLUDE_TESTS} -q -n ${TEST_NQUBITS} -T ${TEST_TYPES} -V ${TEST_QUREG} -p ${TEST_DIR} -g ${TEST_GENERATE}
  COMMAND ${CMAKE_COMMAND} -DBENCHMARKS_EXIST=ON ${QuEST_Project_SOURCE_DIR}
  WORKING_DIRECTORY ${UTIL_ROOT}
  )

if (${BENCHMARKS_EXIST})
  set (INC_CUST "-p ${TEST_DIR}")
else()
  set (INC_CUST "")
endif()

add_test(NAME build
  COMMAND ${CMAKE_MAKE_PROGRAM} "QuESTTest"
  WORKING_DIRECTORY ${QuEST_Project_BINARY_DIR}
  )

if(${ENABLE_ADVANCED_TEST})
  # Get list of test sets
  execute_process(
    COMMAND ${TESTCOMMAND} -Q ${QuEST_LIB_PATH} -L
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
      COMMAND ${TESTCOMMAND} ${INC_CUST} -Q ${QuEST_LIB_PATH} ${TEST}
      )
    set_tests_properties(${TEST}
      PROPERTIES
      DEPANDS build
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
    ${TESTCOMMAND} ${INC_CUST} -Q ${QuEST_LIB_PATH} unit)
  set_tests_properties(unit
    PROPERTIES
    DEPANDS build
    PASS_REGULAR_EXPRESSION " 0 failed"
    FAIL_REGULAR_EXPRESSION "[eE]rror") 
endif()



