"""This module takes care of entrypoints"""

from .promtext import Promtext


def main():
    """main method invoking the core class"""
    Promtext().cli_entrypoint()


if __name__ == "__main__":
    main()
