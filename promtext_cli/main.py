"""Provide the Entrypoints"""

from .promtext import Promtext


def main():
    """Main method invoking the core class"""
    Promtext().cli_entrypoint()


if __name__ == "__main__":
    main()
