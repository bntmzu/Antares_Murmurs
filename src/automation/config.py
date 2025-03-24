from prefect.client.orchestration import get_client


PREFECT_ORION_HOST = "http://localhost:4200"
PREFECT_AGENT_POOL = "default-agent-pool"


def get_prefect_client():
    return get_client(PREFECT_ORION_HOST)
