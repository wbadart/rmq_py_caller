"""single_file.py

This module contains some neat stuff that I'm working on.
created: MAY 2020
"""

def length_of_longest_element(a):
    """Find the longest element of `a` and return its length."""
    longest = max(a, key=len)
    return len(longest)
