# -*- coding: utf-8 -*-
from pathlib import Path
import sys


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.config import config
from src.core.task_registry import (
    get_task,
    get_task_meta,
    get_visible_task_layout,
    register_task,
)


def _flatten(layout):
    names = []
    for item in layout:
        if isinstance(item, list):
            names.extend(item)
        else:
            names.append(item)
    return names


def test_register_task_keeps_legacy_decorator_shape():
    @register_task("pytest legacy task")
    def legacy_task(hwnd):
        return True

    assert get_task("pytest legacy task") is legacy_task
    meta = get_task_meta("pytest legacy task")
    assert meta.name == "pytest legacy task"
    assert meta.ui_config is None
    assert meta.category == "日常任务"
    assert meta.order == 999
    assert meta.row is None
    assert meta.enabled is True


def test_register_task_stores_metadata_and_hides_disabled_tasks():
    ui_config = {
        "fields": [
            {
                "name": "mode",
                "type": "dropdown",
                "label": "模式",
                "options": ["普通", "快速"],
                "default": "普通",
                "value_map": {"普通": "normal", "快速": "fast"},
            }
        ]
    }

    @register_task(
        "pytest metadata task",
        ui_config=ui_config,
        category="pytest",
        order=10,
        row="pytest-row",
        enabled=True,
    )
    def metadata_task(hwnd, task_params=None):
        return True

    @register_task("pytest disabled task", category="pytest", order=11, enabled=False)
    def disabled_task(hwnd):
        return True

    meta = get_task_meta("pytest metadata task")
    assert meta.func is metadata_task
    assert meta.ui_config == ui_config
    assert meta.category == "pytest"
    assert meta.order == 10
    assert meta.row == "pytest-row"
    assert meta.enabled is True

    visible_names = _flatten(get_visible_task_layout())
    assert "pytest metadata task" in visible_names
    assert "pytest disabled task" not in visible_names
    assert get_task("pytest disabled task") is disabled_task


def test_config_daily_tasks_appends_registry_tasks_and_groups_rows():
    @register_task("pytest row task a", category="pytest-layout", order=1, row="pytest-row-layout")
    def row_task_a(hwnd):
        return True

    @register_task("pytest row task b", category="pytest-layout", order=2, row="pytest-row-layout")
    def row_task_b(hwnd):
        return True

    @register_task("pytest solo task", category="pytest-layout", order=3)
    def solo_task(hwnd):
        return True

    layout = config.daily_tasks
    names = _flatten(layout)
    old_names = _flatten(config.task.daily_tasks)
    assert names[: len(old_names)] == old_names
    assert "pytest row task a" in names
    assert "pytest row task b" in names
    assert "pytest solo task" in names
    assert any(
        isinstance(item, list)
        and "pytest row task a" in item
        and "pytest row task b" in item
        for item in layout
    )


def test_registry_ui_config_defaults_and_value_map_are_used_by_config_facade():
    @register_task(
        "pytest ui task",
        ui_config={
            "fields": [
                {
                    "name": "choice",
                    "type": "dropdown",
                    "label": "选项",
                    "options": ["A", "B"],
                    "default": "A",
                    "value_map": {"A": 1, "B": 2},
                }
            ]
        },
        category="pytest-ui",
        order=1,
    )
    def ui_task(hwnd, task_params=None):
        return True

    assert config.has_task_config("pytest ui task")
    assert config.get_task_default_params("pytest ui task") == {"choice": "A"}
    assert config.get_task_mapped_param("pytest ui task", "choice", "B") == 2


def test_legacy_task_definition_has_priority_over_registry_ui_config():
    legacy_task_name = "pytest legacy priority task"
    legacy_definition = {
        "fields": [{"name": "old_field", "type": "text", "default": "old"}]
    }
    config.task_definition.definitions[legacy_task_name] = legacy_definition

    @register_task(
        legacy_task_name,
        ui_config={"fields": [{"name": "new_only", "type": "text", "default": "x"}]},
    )
    def duplicate_legacy_task(hwnd, task_params=None):
        return True

    assert config.get_task_config_definition(legacy_task_name) == legacy_definition
