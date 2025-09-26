#!/usr/bin/env python3
from ...shared.config import set_config
from ...shared.config.cli_adapter import get_cli_config
from .cli import cli
from .evals import add_evals_dataset_item, create_evals_dataset

set_config(get_cli_config())

__all__ = [
    "add_evals_dataset_item",
    "cli",
    "create_evals_dataset",
    # run_evals_workflow removed
    "sync_prompts",
    "update_prompts",
]

if __name__ == "__main__":
    cli()
