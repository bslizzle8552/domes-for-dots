"""Explicit trusted producer registry; package labels never import executable code."""
import procedural_character

BACKENDS = {procedural_character.ID: procedural_character}


def get_backend(identifier):
    try:
        return BACKENDS[identifier]
    except (KeyError, TypeError):
        raise ValueError("unsupported character backend: " + str(identifier)) from None
