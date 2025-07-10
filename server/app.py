import os
from otlp_tracing import configure_oltp_grpc_tracing

from concurrent import futures
import grpc
from server.exception_metadata_interceptor import ExceptionMetadataInterceptor
from server.fishery_service import FisheryService
from server.workflow_service import WorkflowService
from server.stock_assessment_service import StockAssessmentService
from server.ecology_service import EcologyService 
from surimi.v1 import fishery_pb2_grpc, workflow_pb2_grpc, stock_assessment_pb2_grpc, ecology_pb2_grpc

def serve():
    simulation_dictionary = {}

    otel_exporter_otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    print(f"OpenTelemetry tracing configured. Sending to: {otel_exporter_otlp_endpoint}")
    tracer = configure_oltp_grpc_tracing( endpoint=otel_exporter_otlp_endpoint)  # Configure OpenTelemetry tracing

    print(f"AWS_ACCESS_KEY_ID: {os.environ.get('AWS_ACCESS_KEY_ID')}")
    print(f"AWS_SECRET_ACCESS_KEY: {os.environ.get('AWS_SECRET_ACCESS_KEY')}")
    print(f"AWS_SESSION_TOKEN: {os.environ.get('AWS_SESSION_TOKEN')}")
    print(f"AWS_S3_ENDPOINT: {os.environ.get('AWS_S3_ENDPOINT')}")
    print(f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION')}")
    print(f"AWS_BUCKET_NAME: {os.environ.get('AWS_BUCKET_NAME')}")
    print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")}")


    print("Starting gRPC Server...")

    # Create the server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
                         interceptors=[ExceptionMetadataInterceptor()])
    
    workflow_service = WorkflowService(tracer, simulation_dictionary)  # Instantiate the workflow service
    workflow_pb2_grpc.add_WorkflowServiceServicer_to_server(workflow_service, server)

    ecology_service = EcologyService(tracer, simulation_dictionary)  # Instantiate the ecology service
    ecology_pb2_grpc.add_EcologyServiceServicer_to_server(ecology_service, server)

    fishery_service = FisheryService(tracer, simulation_dictionary)  # Instantiate the fishery service
    fishery_pb2_grpc.add_FisheryServiceServicer_to_server(fishery_service, server)

    stock_assessment_service = StockAssessmentService(tracer, simulation_dictionary)  # Instantiate the stock_assessment service
    stock_assessment_pb2_grpc.add_StockAssessmentServiceServicer_to_server(stock_assessment_service, server)

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