"""Traces and eval events, sent to Honeycomb through OpenTelemetry.

Rules for this file:
- It does nothing at all unless HONEYCOMB_API_KEY is set, so the demo and the tests run the same without it.
- No patient data ever goes in an attribute. No names, dates of birth, member ids, packet text or quotes.
  Only ids we make up (case id), counts, codes (CPT), statuses, versions, timings and token counts.
- Every trace carries version tags, so a change in behavior can be tied to the change that caused it.
"""
import contextlib, hashlib, os
from functools import lru_cache

SERVICE = "pa-desk"
_tracer = None
_ready = False


def _versions():
    from .procedures import library
    from .extract_llm import EXTRACT_MODEL, SYSTEM
    from .evidence import VERIFY_MODEL
    return {
        "app.version": os.getenv("PA_APP_VERSION", "0.3.0"),
        "policy.library_version": library().get("version", "unknown"),
        "extract.model": EXTRACT_MODEL,
        "verify.model": VERIFY_MODEL,
        "extract.prompt_hash": hashlib.sha1(SYSTEM.encode()).hexdigest()[:8],
    }


def init():
    """Call once at start. Safe to call again."""
    global _tracer, _ready
    if _ready:
        return bool(_tracer)
    _ready = True
    key = os.getenv("HONEYCOMB_API_KEY")
    if not key:
        return False
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    base = os.getenv("HONEYCOMB_API_ENDPOINT", "https://api.honeycomb.io")  # EU teams: https://api.eu1.honeycomb.io
    try:
        res = {"service.name": SERVICE, "deployment.environment": os.getenv("PA_ENV", "prototype"), **_versions()}
    except Exception:
        res = {"service.name": SERVICE}
    provider = TracerProvider(resource=Resource.create(res))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=base.rstrip("/") + "/v1/traces", headers={"x-honeycomb-team": key})))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(SERVICE)
    return True


class _Null:
    def set_attribute(self, *a, **k): pass
    def set_attributes(self, *a, **k): pass
    def record_exception(self, *a, **k): pass


def _clean(attrs):
    out = {}
    for k, v in attrs.items():
        if v is None:
            continue
        out[k] = v if isinstance(v, (str, bool, int, float)) else str(v)
    return out


@contextlib.contextmanager
def span(name, **attrs):
    """with span("extract.read", n=1) as s: ...  s.set_attribute("x", 1)"""
    init()
    if not _tracer:
        yield _Null()
        return
    with _tracer.start_as_current_span(name, attributes=_clean(attrs)) as s:
        try:
            yield s
        except Exception as e:
            s.record_exception(e)
            s.set_attribute("error", True)
            s.set_attribute("error.type", type(e).__name__)
            raise


def packet_tags():
    """Version tags put on every trace. Missing keys are skipped. Tracing never breaks a case."""
    try:
        init()
        return _versions() if _tracer else {}
    except Exception:
        return {}


def add(**attrs):
    """Add attributes to the span that is running right now."""
    if not _tracer:
        return
    from opentelemetry import trace
    trace.get_current_span().set_attributes(_clean(attrs))


def llm_usage(resp):
    """Record the token counts of an Anthropic reply on the running span."""
    u = getattr(resp, "usage", None)
    if u is not None:
        add(input_tokens=getattr(u, "input_tokens", None), output_tokens=getattr(u, "output_tokens", None),
            cache_read_tokens=getattr(u, "cache_read_input_tokens", None))


def bind(fn):
    """Wrap a function so it runs inside the current trace when called from a worker thread."""
    if not _tracer:
        return fn
    from opentelemetry import context
    ctx = context.get_current()

    def run(*a, **k):
        tok = context.attach(ctx)
        try:
            return fn(*a, **k)
        finally:
            context.detach(tok)
    return run


def event(name, **attrs):
    """A one-off record (a span with no work in it): an eval result, a nurse decision."""
    with span(name, **attrs):
        pass


def flush():
    if _tracer:
        from opentelemetry import trace
        trace.get_tracer_provider().force_flush()
