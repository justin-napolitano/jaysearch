__all__ = ["build_provider_projection", "load_provider_contract", "load_provider_mapping"]


def build_provider_projection(*args, **kwargs):
    from platform_tools.integrations.provider_adapter import build_provider_projection as _impl

    return _impl(*args, **kwargs)


def load_provider_contract(*args, **kwargs):
    from platform_tools.integrations.provider_adapter import load_provider_contract as _impl

    return _impl(*args, **kwargs)


def load_provider_mapping(*args, **kwargs):
    from platform_tools.integrations.provider_adapter import load_provider_mapping as _impl

    return _impl(*args, **kwargs)
