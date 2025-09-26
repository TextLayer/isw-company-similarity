import json


def load_fixture(name: str, ext: str = "txt") -> dict | str:
    try:
        f = open(f"tests/fixtures/{name}.{ext}").read()
        return json.loads(f) if ext == "json" else f
    except Exception as e:
        raise Exception(f"Fixture retrieval failed for {name}") from e


def load_fixture_json(name: str) -> dict:
    return load_fixture(name, "json")


def save_to_fixture(name: str, ext: str = "txt", data: str = None) -> None:
    try:
        with open(f"textlayer/tests/fixtures/{name}.{ext}", "w") as f:
            f.write(data)
    except Exception as e:
        raise Exception(f"Fixture saving failed for {name}") from e


__all__ = ["load_fixture", "save_to_fixture"]
