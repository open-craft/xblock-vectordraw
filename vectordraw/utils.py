"""
This module contains utility functions for the Vector Drawing XBlock.
"""


def get_doc_link(section, link_text="here"):
    """
    Return link to specific `section` of README for Vector Drawing exercises.
    """
    return (
        '<a href="https://github.com/open-craft/jsinput-vectordraw#{section}" target="_blank">'
        '{link_text}'
        '</a>'
    ).format(section=section, link_text=link_text)
