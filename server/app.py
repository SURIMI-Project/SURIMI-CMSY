import os
from otlp_tracing import configure_oltp_grpc_tracing
from concurrent import futures
import grpc
from server.ExceptionMetadataInterceptor import ExceptionMetadataInterceptor
from server.workflow_service import WorkflowService
from server.stock_assessment_service import StockAssessmentService
from server.ecology_service import EcologyService 
from surimi.v1 import workflow_pb2_grpc, stock_assessment_pb2_grpc, ecology_pb2_grpc

def serve():

    simulation_dictionary = {}

    otel_exporter_otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or "http://localhost:4317"

    tracer = configure_oltp_grpc_tracing( endpoint=otel_exporter_otlp_endpoint)  # Configure OpenTelemetry tracing

    print("Starting gRPC Server...")

    # Create the server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
                         interceptors=[ExceptionMetadataInterceptor()])
    
    workflow_service = WorkflowService(tracer, simulation_dictionary)  # Instantiate the workflow service
    workflow_pb2_grpc.add_WorkflowServiceServicer_to_server(workflow_service, server)

    ecology_service = EcologyService(tracer, simulation_dictionary)  # Instantiate the ecology service
    ecology_pb2_grpc.add_EcologyServiceServicer_to_server(ecology_service, server)

    stock_assessment_service = StockAssessmentService(tracer, simulation_dictionary)  # Instantiate the stock_assessment service
    stock_assessment_pb2_grpc.add_StockAssessmentServiceServicer_to_server(stock_assessment_service, server)


    # Bind the server to a port
    server.add_insecure_port("[::]:50201")
    server.start()
    print("[OK] gRPC Server running on port 50201")

    # Wait for the server to stop
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")


if __name__ == "__main__":
    serve()