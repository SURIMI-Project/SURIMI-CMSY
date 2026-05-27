import json
from pathlib import Path

GRPC_MESSAGES_DIR = Path(__file__).parent.parent / "GrpcMessages"


def load_message(message_name: str, filename: str) -> dict:
    """Load a JSON message from GrpcMessages/<message_name>/<filename>.

    Following the naming convention used in the SURIMI-protocol repo,
    e.g. load_message("InitialiseExperiment", "StockAssessmentService_InitialiseExperiment.json")
    """
    path = GRPC_MESSAGES_DIR / message_name / filename
    if not path.exists():
        raise FileNotFoundError(f"Message file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)
