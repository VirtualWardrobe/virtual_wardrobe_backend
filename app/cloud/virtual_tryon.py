from env import env


def _provider_module():
    if env.CLOUD_PROVIDER == "GCP":
        from app.cloud.gcp import vertexai as provider_module
    elif env.CLOUD_PROVIDER == "AWS":
        from app.cloud.aws import nova as provider_module
    else:
        raise ValueError("VW_CLOUD_PROVIDER must be either 'GCP' or 'AWS'")
    return provider_module


async def run_virtual_tryon(
    human_bytes: bytes, garment_bytes: bytes, garment_type: str = "UPPER_BODY"
) -> str:
    return await _provider_module().run_virtual_tryon(
        human_bytes, garment_bytes, garment_type
    )
