from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings

logger = logging.getLogger("waterclaw.otel")


def setup_otel(app: Any, settings: Settings) -> None:
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        logger.warning("OpenTelemetry requested but dependencies are missing: %s", exc)
        return

    provider = TracerProvider(resource=Resource.create({"service.name": "waterclaw-agent-host"}))
    endpoint = settings.otel_exporter_otlp_endpoint
    exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


def current_trace_id() -> str | None:
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None
    return f"{span_context.trace_id:032x}"
