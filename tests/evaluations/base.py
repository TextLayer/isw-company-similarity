import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import cached_property, wraps
from typing import Optional

import pytest

from isw.core.services.llm import ChatClient
from isw.core.utils.llm import extract_output
from isw.shared.config import set_config
from isw.shared.config.cli_adapter import get_cli_config
from isw.shared.logging.logger import logger
from isw.templates.prompts import load_prompt


class FunctionalEvaluator:
    @cached_property
    def chat_client(self) -> ChatClient:
        """Instantiate then cache a chat client for the evaluator"""
        return ChatClient()

    def judge(
        self,
        llm_output: str,
        llm_output_expected: str,
        judge: Optional[str] = "analysis",
        debugging_info: Optional[str] = None,
    ):
        """
        Assert the correctness of the command's LLM output

        Args:
            llm_output: The output of the command.
            llm_output_expected: The expected output of the command.
            judge: The judge prompt to use for the evaluation
        """

        response = self.chat_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": load_prompt(
                        f"{judge}_judge",
                        actual_value=llm_output,
                        expected_value=llm_output_expected,
                    ),
                },
                {
                    "role": "user",
                    "content": "Judge",
                },
            ]
        )

        # Note: eventually could support non-binary judgements
        truthiness = extract_output(response).startswith("1")

        if not truthiness:
            # A rather bold logging error to keep the failing LLM conversation visible
            logger.error(f"""
                \033[91m
                {judge.capitalize()} received the following output:\n\n
                {llm_output} \n
                {debugging_info} \n
                =======================================================
                But expected: \n\n
                {llm_output_expected} \n
                =======================================================
                So the judge determined: \n\n
                {response} \n
                =======================================================
                \033[0m
                """)

        assert truthiness

    @staticmethod
    def sample(size: int = 3, threshold: float = 0.8):
        """
        Decorator to run a test function multiple times in parallel.

        Args:
            size: The number of times to run the test function.
            threshold: The threshold for the test function to pass.
        """

        def decorator(test_func):
            @pytest.mark.integration
            @wraps(test_func)
            def wrapper(*args, **kwargs):
                counters = {
                    "failures": 0,
                    "successes": 0,
                }

                with ThreadPoolExecutor(max_workers=size) as exec:
                    futures = {exec.submit(lambda: test_func(*args, **kwargs)): i for i in range(size)}

                    for future in as_completed(futures):
                        try:
                            future.result()
                            counters["successes"] += 1
                        except Exception:
                            counters["failures"] += 1

                logger.info(f"Passed {counters['successes']} out of {size} tests")

                if (counters["successes"] / (counters["successes"] + counters["failures"])) < threshold:
                    pytest.fail("Test failed to meet required threshold")

            return wrapper

        return decorator

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Configure environment and silence noisy logging"""
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        set_config(get_cli_config())
        yield
