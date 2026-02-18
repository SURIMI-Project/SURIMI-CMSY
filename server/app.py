import os
import grpc

from otlp_tracing import configure_oltp_grpc_tracing
from concurrent import futures
from server.exception_metadata_interceptor import ExceptionMetadataInterceptor
from server.fishery_service import FisheryService
from server.workflow_service import WorkflowService
from server.ecology_service import EcologyService 
from surimi.v1 import fishery_service_pb2_grpc, workflow_service_pb2_grpc, ecology_service_pb2_grpc
from vault_service import VaultService
from dotenv import load_dotenv

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

    otel_exporter_otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    print(f"OpenTelemetry tracing configured. Sending to: {otel_exporter_otlp_endpoint}")
    tracer = configure_oltp_grpc_tracing( endpoint=otel_exporter_otlp_endpoint)  # Configure OpenTelemetry tracing

    print("Starting gRPC Server...")

    # Create the server with 100MB message size limit
    max_message_length = 100 * 1024 * 1024  # 100MB
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ExceptionMetadataInterceptor()],
        options=[
            ('grpc.max_send_message_length', max_message_length),
            ('grpc.max_receive_message_length', max_message_length),
        ]
    )
    
    workflow_service = WorkflowService(tracer, simulation_dictionary)  # Instantiate the workflow service
    workflow_service_pb2_grpc.add_WorkflowServiceServicer_to_server(workflow_service, server)

    ecology_service = EcologyService(tracer, simulation_dictionary)  # Instantiate the ecology service
    ecology_service_pb2_grpc.add_EcologyServiceServicer_to_server(ecology_service, server)

    fishery_service = FisheryService(tracer, simulation_dictionary)  # Instantiate the fishery service
    fishery_service_pb2_grpc.add_FisheryServiceServicer_to_server(fishery_service, server)

    # Bind the server to a port
    server.add_insecure_port("[::]:5020")
    server.start()
    print("[OK] gRPC Server running on port 5020")

    # Wait for the server to stop
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")


if __name__ == "__main__":
    serve()