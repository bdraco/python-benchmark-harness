from ..benchmarking.result_interpreters import ProfilerStatisticsInterpreter
from .._utilities.exceptions import DecoratorCouldNotFindTargetMethod
from ..benchmarking.non_intrusive_profiler import MicroBenchmark
from ..benchmarking.code_instrumentation import Profiler
from functools import wraps, partial
import random
import string


def performance_breakpoint(method, test_case_name, enabled=True):
    """
    This decorator can be used to gather performance statistical
    on a method.
    :param test_case_name: Used to attach a test case name to this decorator.
    :param method: The method that is being profiled
    :param enabled: If True will profile the method under test
    :return: The method output
    """
    # ---------------------------------------------------------------------

    @wraps(method)
    def method_execution(*args, **kwargs):
        """
        An inner function that Will execute the method under test and enable the profiler.
        It will work together with the Results class to formulate a list containing dictionary
        that will store all metrics in a _database or csv file.
        :param args: The Arguments of the method under test
        :param kwargs: The key word arguments of the method under test
        :return: the methods results
        """
        # Setting up the benchmarking object so measurements an tracing can take place
        mb = MicroBenchmark()
        mb.test_case_name = test_case_name

        # Measure and record method performance
        pf = Profiler()
        pf.profile_method_under_test(method, *args, **kwargs)

        # Extract and upload method performance statistics
        ProfilerStatisticsInterpreter(
            performance_statistics=pf.performance_statistics,
            total_response_time=pf.total_response_time,
            test_case_name=mb.test_case_name,
            connection_url=mb.database_connection_url,
            test_id=mb.current_test_id,
            method_name=method.__name__,
            sample_id=''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        )

        return pf.functional_output

    # ---------------------------------------------------------------------

    if method is None:
        return partial(performance_breakpoint, test_case_name=test_case_name, enabled=enabled)

    elif callable(method) is not True:
        raise DecoratorCouldNotFindTargetMethod()

    else:
        # Execute the method under test
        output = method_execution
        return output
