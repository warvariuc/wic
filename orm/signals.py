"""Signals for ORM
"""

from dispatch import Signal


pre_save = Signal(providing_args=['record'])
post_save = Signal(providing_args=['record', 'is_new'])

pre_delete = Signal(providing_args=['record'])
post_delete = Signal(providing_args=['record'])
