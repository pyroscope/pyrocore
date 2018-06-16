# The default PyroScope configuration script
#
# For details, see https://pyrocore.readthedocs.io/en/latest/setup.html
# and https://pyrocore.readthedocs.io/en/latest/custom.html#defining-custom-fields
#

def _custom_fields():
    """ Yield custom field definitions.
    """
    # Import some commonly needed modules
    import os
    from pyrocore.torrent import engine, matching
    from pyrocore.util import fmt

    # PUT CUSTOM FIELD CODE HERE

    # Disk space check (as an example)
    # see https://pyrocore.readthedocs.io/en/latest/custom.html#has-room
    def has_room(obj):
        "Check disk space."
        pathname = obj.path
        if pathname and not os.path.exists(pathname):
            pathname = os.path.dirname(pathname)
        if pathname and os.path.exists(pathname):
            stats = os.statvfs(pathname)
            return (stats.f_bavail * stats.f_frsize - int(diskspace_threshold_mb) * 1024**2
                > obj.size * (1.0 - obj.done / 100.0))
        else:
            return None

    yield engine.DynamicField(engine.untyped, "has_room",
        "check whether the download will fit on its target device",
        matcher=matching.BoolFilter, accessor=has_room,
        formatter=lambda val: "OK" if val else "??" if val is None else "NO")
    globals().setdefault("diskspace_threshold_mb", "500")


# Register our factory with the system
custom_field_factories.append(_custom_fields)
