"""Unit tests for omnibench.gateway — protocol, adapters, router."""

import pytest


class TestGatewayRequest:
    def test_basic_construction(self):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="click the button")
        assert req.prompt == "click the button"
        assert req.temperature == 0.1
        assert req.max_tokens == 256

    def test_invalid_temperature_raises(self):
        from omnibench.gateway.protocol import GatewayRequest
        with pytest.raises(ValueError):
            GatewayRequest(prompt="x", temperature=5.0)

    def test_invalid_max_tokens_raises(self):
        from omnibench.gateway.protocol import GatewayRequest
        with pytest.raises(ValueError):
            GatewayRequest(prompt="x", max_tokens=0)

    def test_non_string_prompt_raises(self):
        from omnibench.gateway.protocol import GatewayRequest
        with pytest.raises(TypeError):
            GatewayRequest(prompt=123)

    def test_images_default_empty(self):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="test")
        assert req.images == []


class TestGatewayResponse:
    def test_success_true_when_no_error(self):
        from omnibench.gateway.protocol import GatewayResponse
        resp = GatewayResponse(
            text="result", action_json={}, usage_tokens=10,
            latency_ms=50.0, provider_used="mock"
        )
        assert resp.success is True

    def test_success_false_when_error(self):
        from omnibench.gateway.protocol import GatewayResponse
        resp = GatewayResponse(
            text="", action_json={}, usage_tokens=0,
            latency_ms=0.0, provider_used="mock", error="oops"
        )
        assert resp.success is False

    def test_error_response_factory(self):
        from omnibench.gateway.protocol import GatewayResponse
        resp = GatewayResponse.error_response("fail", "test_provider", 10.0)
        assert resp.error == "fail"
        assert resp.provider_used == "test_provider"
        assert resp.success is False


class TestMockAdapter:
    def test_is_available(self, mock_adapter):
        assert mock_adapter.is_available() is True

    def test_generate_returns_response(self, mock_adapter, gateway_request):
        resp = mock_adapter.generate(gateway_request)
        assert resp.success is True
        assert isinstance(resp.text, str)
        assert isinstance(resp.action_json, dict)
        assert resp.provider_used == "mock"

    def test_deterministic_output(self, mock_adapter):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="deterministic_test_prompt_xyz")
        r1 = mock_adapter.generate(req)
        r2 = mock_adapter.generate(req)
        assert r1.text == r2.text

    def test_with_images(self, mock_adapter, image_bytes):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="describe screen", images=[image_bytes])
        resp = mock_adapter.generate(req)
        assert resp.success is True

    def test_latency_is_positive(self, mock_adapter, gateway_request):
        resp = mock_adapter.generate(gateway_request)
        assert resp.latency_ms >= 0


class TestLocalONNXAdapter:
    def test_is_available_when_onnxruntime_installed(self):
        from omnibench.gateway.adapters import LocalONNXAdapter
        adapter = LocalONNXAdapter()
        # Just check it doesn't raise
        result = adapter.is_available()
        assert isinstance(result, bool)

    def test_generate_returns_response(self, blank_image):
        from omnibench.gateway.adapters import LocalONNXAdapter
        from omnibench.gateway.protocol import GatewayRequest
        import io
        buf = io.BytesIO()
        blank_image.save(buf, format="PNG")
        req = GatewayRequest(prompt="click the blue button", images=[buf.getvalue()])
        adapter = LocalONNXAdapter()
        resp = adapter.generate(req)
        assert isinstance(resp.text, str)
        assert isinstance(resp.action_json, dict)


class TestCascadingRouter:
    def test_routes_to_mock(self, mock_router, gateway_request):
        resp = mock_router.route(gateway_request)
        assert resp.success is True

    def test_available_providers(self, mock_router):
        providers = mock_router.available_providers()
        assert isinstance(providers, list)
        assert len(providers) >= 1

    def test_fallback_when_primary_unavailable(self):
        from omnibench.gateway.adapters import MockAdapter
        from omnibench.gateway.router import CascadingRouter
        from omnibench.gateway.protocol import GatewayRequest

        class UnavailableAdapter(MockAdapter):
            name = "unavailable"
            def is_available(self): return False

        router = CascadingRouter(adapters=[UnavailableAdapter()], mock_fallback=True)
        req = GatewayRequest(prompt="test fallback")
        resp = router.route(req)
        assert resp.success is True

    def test_error_response_when_all_fail(self):
        from omnibench.gateway.router import CascadingRouter
        from omnibench.gateway.protocol import GatewayRequest

        router = CascadingRouter(adapters=[], mock_fallback=False)
        # Override local adapter to be unavailable too
        from omnibench.gateway.adapters import MockAdapter
        class NeverAvailable(MockAdapter):
            def is_available(self): return False
        router._local_adapter = NeverAvailable()
        req = GatewayRequest(prompt="test")
        resp = router.route(req)
        assert resp.success is False

    def test_add_adapter(self, mock_adapter):
        from omnibench.gateway.router import CascadingRouter
        router = CascadingRouter()
        router.add_adapter(mock_adapter, priority=0)
        assert len(router._adapters) == 1
