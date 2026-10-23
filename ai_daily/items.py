"""Legacy label compatibility; newspaper sources use report.source_name."""


def source_label(name, day):
    return f"{name} · {day:%m-%d}"
