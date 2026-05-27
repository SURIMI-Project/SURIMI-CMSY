
from grpc_interceptor.exceptions import GrpcException
import grpc


def log_and_abort(context, status_code, message):
    """
    Logs an error message and aborts the gRPC call with the given status code.
    Raises GrpcException so the handler stops executing immediately.
    """
    print(f"Error: {message}")  # Log the error message
    context.abort(status_code, message)  # Abort the gRPC call with the specified status code and message
    raise GrpcException(status_code, message)  # Stop execution in the handler