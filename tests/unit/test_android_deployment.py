"""Unit tests for Android deployment primitives & Samsung contact calling tasks."""

import pytest
from omnibench.drivers.android import AndroidDriver
from omnibench.benchmarks.adapters.androidworld import AndroidWorldAdapter


class TestAndroidDeploymentPrimitives:
    def test_call_contact_mock_mode(self):
        driver = AndroidDriver(mock=True)
        driver.connect()
        res = driver.call_contact("Vanya Chaudhary")
        assert res.success is True
        assert res.action_type == "call_contact"
        assert res.params["contact"] == "Vanya Chaudhary"
        assert len(driver.history) >= 1
        assert driver.history[-1]["action"] == "call_contact"

    def test_launch_app_mock_mode(self):
        driver = AndroidDriver(mock=True)
        driver.connect()
        res = driver.launch_app("com.samsung.android.dialer")
        assert res.success is True
        assert res.action_type == "launch_app"
        assert res.params["package_name"] == "com.samsung.android.dialer"

    def test_android_adapter_contains_vanya_task(self):
        adapter = AndroidWorldAdapter()
        tasks = adapter.load_tasks()
        task_ids = [t.task_id for t in tasks]
        assert "android_samsung_call_vanya_001" in task_ids
        call_task = next(t for t in tasks if t.task_id == "android_samsung_call_vanya_001")
        assert "Vanya Chaudhary" in call_task.instruction
        assert call_task.platform == "android"
