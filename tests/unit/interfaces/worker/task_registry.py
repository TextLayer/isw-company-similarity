import time
import unittest
from unittest.mock import Mock, patch

import pytest

from isw.core.errors import ValidationException
from isw.interfaces.worker.registry import task_registry

retry_count = 0


def invalid_task_with_no_param():
    pass


def invalid_task_with_no_param_type(a):
    pass


def invalid_task_with_too_many_params(a, b):
    pass


def invalid_task_with_wrong_param_type(a: str):
    pass


def valid_task(data: dict):
    pass


def valid_task_with_fail(data: dict):
    global retry_count
    retry_count += 1

    if retry_count < 2:
        raise Exception("Failed")

    return True


class TestTaskRegistry(unittest.TestCase):
    def test_task_parameter_validation(self):
        task_registry.register(valid_task)

        with pytest.raises(ValidationException):
            task_registry.register(invalid_task_with_no_param)
        with pytest.raises(ValidationException):
            task_registry.register(invalid_task_with_no_param_type)
        with pytest.raises(ValidationException):
            task_registry.register(invalid_task_with_too_many_params)
        with pytest.raises(ValidationException):
            task_registry.register(invalid_task_with_wrong_param_type)

    def test_invoke_known_task(self):
        mock_task = Mock()
        mock_task.delay.return_value.get.return_value = True
        mock_tasks_internal = {
            "known_task": mock_task,
        }

        with patch.object(task_registry, "_tasks", mock_tasks_internal):
            assert task_registry.defer("known_task")

            with pytest.raises(ValidationException):
                task_registry.defer("unknown_task")

    def test_task_retry(self):
        task_registry.register(valid_task_with_fail)

        assert task_registry.defer("valid_task_with_fail")

        time.sleep(30)
        assert retry_count == 2
