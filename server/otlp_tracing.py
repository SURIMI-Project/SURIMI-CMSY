from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry import trace

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer

def configure_oltp_grpc_tracing(endpoint: str = None) -> trace.Tracer:
    resource = Resource(attributes={ SERVICE_NAME: "surimi-cmsy"})

    GrpcInstrumentorServer().instrument()

    # Configure Tracing
    traceProvider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    traceProvider.add_span_processor(processor)
    trace.set_tracer_provider(traceProvider)

    # Configure Metrics
    # reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
    # meterProvider = MeterProvider(metric_readers=[reader])
    # metrics.set_meter_provider(meterProvider)

    # Configure Logging
    # logger_provider = LoggerProvider()
    # set_logger_provider(logger_provider)

    # exporter = OTLPLogExporter(endpoint=endpoint)
    # logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    # handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    # handler.setFormatter(logging.Formatter("Python: %(message)s"))

    # Attach OTLP handler to root logger
    # logging.getLogger().addHandler(handler)

    tracer = trace.get_tracer(__name__)
    return tracer