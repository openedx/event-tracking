#!/usr/bin/env python
"""Manage.py file for testing event tracking"""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventtracking.django.tests.env.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
