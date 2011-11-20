from dispatch import Signal

pre_save = Signal(providing_args=["instance", "raw", "using"])
post_save = Signal(providing_args=["instance", "raw", "created", "using"])

pre_delete = Signal(providing_args=["instance", "using"])
post_delete = Signal(providing_args=["instance", "using"])
