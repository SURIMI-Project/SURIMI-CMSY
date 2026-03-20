import os
import grpc

from otlp_tracing import configure_oltp_grpc_tracing
from concurrent import futures
from server.exception_metadata_interceptor import ExceptionMetadataInterceptor
from server.version_metadata_interceptor import VersionMetadataInterceptor
from server.catch_consumer_service import CatchConsumerService
from server.workflow_service import WorkflowService
from server.ecology_consumer_service import EcologyConsumerService 
from surimi.v1 import catch_consumer_service_pb2_grpc, workflow_service_pb2_grpc, ecology_consumer_service_pb2_grpc
from vault_service import VaultService
from dotenv import load_dotenv
from importlib.metadata import version, PackageNotFoundError

def serve():
    load_dotenv()  # Load environment variables from .env file

    # Simulation storage shared across services
    simulation_dictionary = {}

    VaultService.LoadVaultSecretsInEnvironmentVariables()  # Load secrets from Vault into environment variables

    # Print all environment variables
    print("=" * 80)
    print("Environment Variables:")
    print("=" * 80)
    for key, value in sorted(os.environ.items()):
        print(f"{key}: {value}")
    print("=" * 80)

    version = load_version("surimi_surimi_protocol_grpc_python")
    print("Starting gRPC Server... with protocol version:", version)

    otel_exporter_otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    print(f"OpenTelemetry tracing configured. Sending to: {otel_exporter_otlp_endpoint}")
    tracer = configure_oltp_grpc_tracing( endpoint=otel_exporter_otlp_endpoint)  # Configure OpenTelemetry tracing

    print("Starting gRPC Server...")

    # Create the server with 100MB message size limit
    max_message_length = 100 * 1024 * 1024  # 100MB
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ExceptionMetadataInterceptor(), VersionMetadataInterceptor(version)],
        options=[
            ('grpc.max_send_message_length', max_message_length),
            ('grpc.max_receive_message_length', max_message_length),
        ]
    )
    
    workflow_service = WorkflowService(tracer, simulation_dictionary, version)  # Instantiate the workflow service
    workflow_service_pb2_grpc.add_WorkflowServiceServicer_to_server(workflow_service, server)

    ecology_consumer_service = EcologyConsumerService(tracer, simulation_dictionary)  # Instantiate the ecology service
    ecology_consumer_service_pb2_grpc.add_EcologyConsumerServiceServicer_to_server(ecology_consumer_service, server)

    catch_consumer_service = CatchConsumerService(tracer, simulation_dictionary)  # Instantiate the catch consumer service
    catch_consumer_service_pb2_grpc.add_CatchConsumerServiceServicer_to_server(catch_consumer_service, server)

    # Bind the server to a port
    server.add_insecure_port("[::]:5021")
    server.start()
    print("[OK] gRPC Server running on port 5021")

    # Wait for the server to stop
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")

def load_version(package_name: str) -> str:
    try:
        # Example: "1.78.10101.47+7fb5c33e314a"
        package_version = version(package_name)
        return package_version.split("+", 1)[1] if "+" in package_version else package_version
    except PackageNotFoundError:
        return "unknown"

if __name__ == "__main__":
    serve()