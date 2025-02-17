"""
Test for environment variable handling
"""

from parameterized import parameterized, param
from unittest import TestCase
from samcli.local.lambdafn.env_vars import EnvironmentVariables


class TestEnvironmentVariables_init(TestCase):
    def test_must_initialize_with_empty_values(self):

        memory = 123
        timeout = 10
        handler = "handler"

        environ = EnvironmentVariables()
        environ.memory = memory
        environ.timeout = timeout
        environ.handler = handler

        self.assertEquals(environ.memory, memory)
        self.assertEquals(environ.timeout, timeout)
        self.assertEquals(environ.handler, handler)

    def test_must_initialize_values_with_required_values(self):
        memory = 123
        timeout = 10
        handler = "handler"

        environ = EnvironmentVariables(memory, timeout, handler)
        self.assertEquals(environ.memory, memory)
        self.assertEquals(environ.timeout, timeout)
        self.assertEquals(environ.handler, handler)
        self.assertEquals(environ.variables, {})
        self.assertEquals(environ.shell_env_values, {})
        self.assertEquals(environ.override_values, {})
        self.assertEquals(environ.aws_creds, {})

    def test_must_initialize_with_optional_values(self):
        memory = 123
        timeout = 10
        handler = "handler"
        variables = {"a": "b"}
        shell_values = {"c": "d"}
        overrides = {"e": "f"}
        aws_creds = {"g": "h"}

        environ = EnvironmentVariables(
            memory,
            timeout,
            handler,
            variables=variables,
            shell_env_values=shell_values,
            override_values=overrides,
            aws_creds=aws_creds,
        )

        self.assertEquals(environ.variables, {"a": "b"})
        self.assertEquals(environ.shell_env_values, {"c": "d"})
        self.assertEquals(environ.override_values, {"e": "f"})
        self.assertEquals(environ.aws_creds, {"g": "h"})


class TestEnvironmentVariables_resolve(TestCase):
    def setUp(self):
        self.memory = 1024
        self.timeout = 123
        self.handler = "handler"

        self.aws_creds = {
            "region": "some region",
            "key": "some key",
            "secret": "some other secret",
            "sessiontoken": "some other token",
        }

        self.variables = {
            "variable1": 1,
            "variable2": "mystring",
            "list_var": [1, 2, 3],
            "dict_var": {"a": {"b": "c"}},
            "none_var": None,
            "true_var": True,
            "false_var": False,
            # We should be able to override AWS_*  values
            "AWS_DEFAULT_REGION": "user-specified-region",
        }

        self.shell_env = {
            # This variable is not defined in self.variables. So won't show up in resutlt
            "myothervar": "somevalue",
            "variable1": "variable1 value from shell_env",
        }

        self.override = {
            # This variable is not defined in self.variables. So won't show up in resutlt
            "unknown_var": "newvalue",
            "variable1": "variable1 value from overrides",
            "list_var": "list value coming from overrides",
        }

    def test_with_no_additional_variables(self):
        """
        Test assuming user has *not* passed any environment variables. Only AWS variables should be setup
        """

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            "AWS_REGION": "some region",
            "AWS_DEFAULT_REGION": "some region",
            "AWS_ACCESS_KEY_ID": "some key",
            "AWS_SECRET_ACCESS_KEY": "some other secret",
            "AWS_SESSION_TOKEN": "some other token",
        }

        environ = EnvironmentVariables(self.memory, self.timeout, self.handler, aws_creds=self.aws_creds)

        result = environ.resolve()

        # With no additional environment variables, resolve() should just return all AWS variables
        self.assertEquals(result, expected)

    def test_with_only_default_values_for_variables(self):
        """
        Given only environment variable values, without any shell env values or overridden values
        """

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "defaultkey",
            "AWS_SECRET_ACCESS_KEY": "defaultsecret",
            # This value is coming from user passed environment variable
            "AWS_DEFAULT_REGION": "user-specified-region",
            "variable1": "1",
            "variable2": "mystring",
            "list_var": "",
            "dict_var": "",
            "none_var": "",
            "true_var": "true",
            "false_var": "false",
        }

        environ = EnvironmentVariables(self.memory, self.timeout, self.handler, variables=self.variables)

        self.assertEquals(environ.resolve(), expected)

    def test_with_shell_env_value(self):
        """
        Given values for the variables from shell environment
        """

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "defaultkey",
            "AWS_SECRET_ACCESS_KEY": "defaultsecret",
            # This value is coming from user passed environment variable
            "AWS_DEFAULT_REGION": "user-specified-region",
            # Value coming from the shell
            "variable1": "variable1 value from shell_env",
            "variable2": "mystring",
            "list_var": "",
            "dict_var": "",
            "none_var": "",
            "true_var": "true",
            "false_var": "false",
        }

        environ = EnvironmentVariables(
            self.memory, self.timeout, self.handler, variables=self.variables, shell_env_values=self.shell_env
        )

        self.assertEquals(environ.resolve(), expected)

    def test_with_overrides_value(self):
        """
        Given values for the variables from user specified overrides
        """

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "defaultkey",
            "AWS_SECRET_ACCESS_KEY": "defaultsecret",
            # This value is coming from user passed environment variable
            "AWS_DEFAULT_REGION": "user-specified-region",
            "variable2": "mystring",
            # Value coming from the overrides
            "variable1": "variable1 value from overrides",
            "list_var": "list value coming from overrides",
            "dict_var": "",
            "none_var": "",
            "true_var": "true",
            "false_var": "false",
        }

        environ = EnvironmentVariables(
            self.memory,
            self.timeout,
            self.handler,
            variables=self.variables,
            shell_env_values=self.shell_env,
            override_values=self.override,
        )

        self.assertEquals(environ.resolve(), expected)


class TestEnvironmentVariables_get_aws_variables(TestCase):
    def setUp(self):
        self.memory = 1024
        self.timeout = 123
        self.handler = "handler"

        self.aws_creds = {
            "region": "some region",
            "key": "some key",
            "secret": "some other secret",
            "sessiontoken": "some other token",
        }

    def test_must_work_with_overridden_aws_creds(self):

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            "AWS_REGION": "some region",
            "AWS_DEFAULT_REGION": "some region",
            "AWS_ACCESS_KEY_ID": "some key",
            "AWS_SECRET_ACCESS_KEY": "some other secret",
            "AWS_SESSION_TOKEN": "some other token",
        }

        environ = EnvironmentVariables(self.memory, self.timeout, self.handler, aws_creds=self.aws_creds)

        self.assertEquals(expected, environ._get_aws_variables())

    def test_must_work_without_any_aws_creds(self):

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            # Default values assigned to these variables
            "AWS_REGION": "us-east-1",
            "AWS_DEFAULT_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "defaultkey",
            "AWS_SECRET_ACCESS_KEY": "defaultsecret",
        }

        environ = EnvironmentVariables(self.memory, self.timeout, self.handler)
        self.assertEquals(expected, environ._get_aws_variables())

    def test_must_work_with_partial_aws_creds(self):

        creds = {"region": "some other region", "sessiontoken": "my awesome token"}

        expected = {
            "AWS_SAM_LOCAL": "true",
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "1024",
            "AWS_LAMBDA_FUNCTION_TIMEOUT": "123",
            "AWS_LAMBDA_FUNCTION_HANDLER": "handler",
            # Values from the input creds
            "AWS_REGION": "some other region",
            "AWS_DEFAULT_REGION": "some other region",
            "AWS_SESSION_TOKEN": "my awesome token",
            # These variables still get the default value
            "AWS_ACCESS_KEY_ID": "defaultkey",
            "AWS_SECRET_ACCESS_KEY": "defaultsecret",
        }

        environ = EnvironmentVariables(self.memory, self.timeout, self.handler, aws_creds=creds)
        self.assertEquals(expected, environ._get_aws_variables())


class TestEnvironmentVariables_stringify_value(TestCase):
    def setUp(self):

        self.environ = EnvironmentVariables(1024, 10, "handler")

    @parameterized.expand([param([1, 2, 3]), param({"a": {"b": "c"}}), param(("this", "is", "tuple")), param(None)])
    def test_must_replace_non_scalar_with_blank_values(self, input):
        self.assertEquals("", self.environ._stringify_value(input))

    @parameterized.expand(
        [
            (True, "true"),
            (False, "false"),
            (1234, "1234"),
            (3.14, "3.14"),
            (u"mystring\xe0", u"mystring\xe0"),
            ("mystring", "mystring"),
        ]
    )
    def test_must_stringify(self, input, expected):
        self.assertEquals(expected, self.environ._stringify_value(input))


class TestEnvironmentVariables_add_lambda_event_body(TestCase):
    def test_must_add_proper_variable(self):

        value = "foobar"

        environ = EnvironmentVariables()
        environ.add_lambda_event_body(value)

        self.assertEquals(environ.variables.get("AWS_LAMBDA_EVENT_BODY"), value)
