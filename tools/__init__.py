# -*- coding: utf-8 -*-
import enum


class colors:
    GREEN = "\033[92m"
    FAIL = "\033[91m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"


class RepositoryType(enum.Enum):
    github = enum.auto()
    gitlab = enum.auto()
