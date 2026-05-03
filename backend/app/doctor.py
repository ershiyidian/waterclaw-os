from __future__ import annotations


def main() -> None:
    import fastapi  # noqa: F401
    import litellm  # noqa: F401
    import pydantic  # noqa: F401

    print("python backend imports ok")


if __name__ == "__main__":
    main()
