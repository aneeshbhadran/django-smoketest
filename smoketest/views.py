from django.http import HttpResponse
from django.conf import settings
from django.utils import simplejson
import inspect
import importlib
from smoketest import SmokeTest, ApplicationTestResultSet


def test_class(cls):
    o = cls()
    return o.run()

def test_application(app):
    """ should return an ApplicationTestResultSet """
    num_test_classes = 0
    num_tests_run = 0
    num_tests_passed = 0
    num_tests_failed = 0
    num_tests_errored = 0

    failed_tests = []
    errored_tests = []

    try:
        a = importlib.import_module("%s.smoke" % app)
        for name, obj in inspect.getmembers(a, inspect.isclass):
            if not issubclass(obj, SmokeTest):
                continue
            if name == "SmokeTest":
                # skip the parent class, which is usually imported
                continue
            num_test_classes += 1
            (run, passed, failed, errored,
             f_tests, e_tests) = test_class(obj)
            num_tests_run += run
            num_tests_passed += passed
            num_tests_failed += failed
            num_tests_errored += errored
            failed_tests = failed_tests + f_tests
            errored_tests = errored_tests + e_tests

    except ImportError:
        # no 'smokes' module for the app
        pass
    except Exception, e:
        # anything else, probably an error in setUp()
        # or tearDown()
        num_tests_errored += 1
    return ApplicationTestResultSet(
        num_test_classes, num_tests_run,
        num_tests_passed, num_tests_errored,
        num_tests_failed, failed_tests,
        errored_tests)

def make_failed_report(result_sets):
    fails = []
    if sum([r.num_tests_failed for r in result_sets]) == 0:
        return ""
    for r in result_sets:
        if r.num_tests_failed > 0:
            for f in r.failed:
                fails.append(f)
    return "\n".join(["%s failed" % f for f in fails])

def make_errored_report(result_sets):
    errors = []
    if sum([r.num_tests_errored for r in result_sets]) == 0:
        return ""
    for r in result_sets:
        if r.num_tests_errored > 0:
            for f in r.errored:
                errors.append(f)
    return "\n".join(["%s errored" % e for e in errors])


def index(request):
    result_sets = [test_application(app) for app in settings.INSTALLED_APPS]
    all_passed = reduce(lambda x, y: x & y, [r.passed() for r in result_sets])
    num_test_classes = sum([r.num_test_classes for r in result_sets])
    num_tests_run = sum([r.num_tests_run for r in result_sets])
    num_tests_passed = sum([r.num_tests_passed for r in result_sets])
    num_tests_failed = sum([r.num_tests_failed for r in result_sets])
    num_tests_errored = sum([r.num_tests_errored for r in result_sets])
    failed_report = make_failed_report(result_sets)
    errored_report = make_errored_report(result_sets)
    if all_passed:
        status = "PASS"
    else:
        status = "FAIL"
    if 'application/json' in request.META['HTTP_ACCEPT']:
        return HttpResponse(
            simplejson.dumps(
                dict(
                    status=status,
                    test_classes=num_test_classes,
                    tests_run=num_tests_run,
                    tests_passed=num_tests_passed,
                    tests_failed=num_tests_failed,
                    tests_errored=num_tests_errored,
                    failed_tests=reduce(lambda x, y: x + y,
                                        [r.failed for r in result_sets]),
                    errored_tests=reduce(lambda x, y: x + y,
                                        [r.errored for r in result_sets]),
                    )),
            content_type="application/json",
            )
    else:
        return HttpResponse(
        """%s
test classes: %d
tests run: %d
tests passed: %d
tests failed: %d
tests errored: %d
%s
%s""" % (status, num_test_classes, num_tests_run, num_tests_passed,
         num_tests_failed, num_tests_errored, failed_report,
         errored_report))
