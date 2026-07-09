import logging
from server.logging_formatter import _ConditionalLoggingLevelFormatter

_handler = logging.StreamHandler()
_handler.setFormatter(_ConditionalLoggingLevelFormatter())
logging.root.addHandler(_handler)
logging.root.setLevel(logging.DEBUG)

import os
import grpc

from concurrent import futures
from server.exception_metadata_interceptor import ExceptionMetadataInterceptor
from server.version_metadata_interceptor import VersionMetadataInterceptor
from server.StockAssessment import StockAssessmentService
from surimi.v1 import stock_assessment_service_pb2_grpc, stock_assessment_service_pb2
from vault_service import VaultService
from dotenv import load_dotenv
from importlib.metadata import version, PackageNotFoundError
from grpc_reflection.v1alpha import reflection

def _build_server():
    """Initialise and start the gRPC server, return the server instance."""
    load_dotenv()  # Load environment variables from .env file

    # Experiment storage shared across services
    experiment_dictionary = {}

    VaultService.LoadVaultSecretsInEnvironmentVariables()  # Load secrets from Vault into environment variables

    # Print all environment variables
    logging.info("=" * 80)
    logging.info("Environment Variables:")
    logging.info("=" * 80)
    for key, value in sorted(os.environ.items()):
        logging.info(f"{key}: {value}")
    logging.info("=" * 80)

    ver = load_version("surimi_surimi_protocol_grpc_python")
    logging.info(f"Starting gRPC Server... with protocol version: {ver}")

    logging.info("Starting gRPC Server...")

    # Create the server with 100MB message size limit
    max_message_length = 100 * 1024 * 1024  # 100MB
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ExceptionMetadataInterceptor(), VersionMetadataInterceptor(ver)],
        options=[
            ('grpc.max_send_message_length', max_message_length),
            ('grpc.max_receive_message_length', max_message_length),
        ]
    )

    stock_assessment_service = StockAssessmentService(experiment_dictionary, ver)
    stock_assessment_service_pb2_grpc.add_StockAssessmentServiceServicer_to_server(stock_assessment_service, server)

    # the reflection service will be aware of "StockAssessmentService" and "ServerReflection" services.
    SERVICE_NAMES = (
        stock_assessment_service_pb2.DESCRIPTOR.services_by_name['StockAssessmentService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    # Bind the server to a port
    server.add_insecure_port("[::]:5021")
    server.start()
    logging.info("[OK] gRPC Server running on port 5021")
    return server


def serve():
    """Blocking entry point used when running server/app.py directly."""
    server = _build_server()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("\n[INFO] Server shutting down...")


def serve_in_thread():
    """Non-blocking entry point for in-process use (e.g. integration tests).

    Starts the gRPC server and returns immediately so the calling thread
    (typically a daemon thread) can keep the server alive.
    """
    server = _build_server()  # Keep reference alive to prevent GC from stopping the server
    import time
    while True:
        time.sleep(3600)

def load_version(package_name: str) -> str:
    try:
        # Example: "1.78.10101.47+7fb5c33e314a"
        package_version = version(package_name)
        return package_version.split("+", 1)[1] if "+" in package_version else package_version
    except PackageNotFoundError:
        return "unknown"

if __name__ == "__main__":
    serve()