import json
from pathlib import Path

GRPC_MESSAGES_DIR = Path(__file__).parent.parent / "GrpcMessages"


def load_message(message_name: str) -> dict:
    """Load the JSON message from the GrpcMessages/<message_name>/ directory.

    Finds the first .json file in the directory, so the filename does not need
    to be hardcoded. Following the naming convention used in the SURIMI-protocol
    repo (e.g. StockAssesmentService_InitialiseExperiment.json).
    """
    directory = GRPC_MESSAGES_DIR / message_name
    json_files = list(directory.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No .json file found in: {directory}")
    with open(json_files[0], "r") as f:
        return json.load(f)
