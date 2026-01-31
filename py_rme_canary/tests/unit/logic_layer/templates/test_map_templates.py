"""
Tests for map template definitions.

Following Sonnet TDD workflow with strict assertions.
"""

import pytest
from py_rme_canary.logic_layer.templates.map_templates import (
    ALL_TEMPLATES,
    COMMON_MAP_SIZES,
    MAP_SIZE_MEDIUM,
    MAP_SIZE_SMALL,
    TEMPLATE_7_4,
    TEMPLATE_8_6,
    TEMPLATE_12_0,
    MapSize,
    TibiaVersion,
    get_template_by_name,
    get_template_by_version,
)


def test_tibia_version_enum():
    """Test Tibia version enum values."""
    assert TibiaVersion.V7_4 == "7.4"
    assert TibiaVersion.V8_6 == "8.6"
    assert TibiaVersion.V12_0 == "12.0"
    assert TibiaVersion.CUSTOM == "custom"


def test_map_size_creation():
    """Test MapSize creation and properties."""
    size = MapSize(2048, 2048)
    assert size.width == 2048
    assert size.height == 2048
    assert size.name == "Small (2048x2048)"


def test_map_size_names():
    """Test MapSize name generation for common sizes."""
    assert MAP_SIZE_SMALL.name == "Small (2048x2048)"
    assert MAP_SIZE_MEDIUM.name == "Medium (4096x4096)"

    # Custom size
    custom = MapSize(1024, 1024)
    assert custom.name == "Custom (1024x1024)"


def test_common_map_sizes_count():
    """Test that we have 4 common map sizes."""
    assert len(COMMON_MAP_SIZES) == 4


def test_all_templates_count():
    """Test that we have 7 predefined templates."""
    assert len(ALL_TEMPLATES) == 7


def test_template_7_4_properties():
    """Test Tibia 7.4 template has correct properties."""
    assert TEMPLATE_7_4.name == "Tibia 7.4 (Classic)"
    assert TEMPLATE_7_4.version == TibiaVersion.V7_4
    assert TEMPLATE_7_4.otbm_version == 2
    assert TEMPLATE_7_4.use_client_ids is False
    assert TEMPLATE_7_4.spawn_file_enabled is True
    assert TEMPLATE_7_4.house_file_enabled is True


def test_template_8_6_properties():
    """Test Tibia 8.6 template has correct properties."""
    assert TEMPLATE_8_6.name == "Tibia 8.6"
    assert TEMPLATE_8_6.version == TibiaVersion.V8_6
    assert TEMPLATE_8_6.otbm_version == 2
    assert TEMPLATE_8_6.use_client_ids is False


def test_template_12_uses_client_ids():
    """Test Tibia 12.x template uses ClientID format."""
    assert TEMPLATE_12_0.use_client_ids is True
    assert TEMPLATE_12_0.otbm_version == 5


def test_get_template_by_version():
    """Test retrieving template by Tibia version."""
    template = get_template_by_version(TibiaVersion.V7_4)
    assert template.version == TibiaVersion.V7_4
    assert template == TEMPLATE_7_4


def test_get_template_by_version_not_found():
    """Test get_template_by_version raises for invalid version."""
    # Create invalid enum value (only for testing)
    with pytest.raises(ValueError, match="No template found for version"):
        # This will fail because we're checking all templates
        class FakeVersion:
            pass

        get_template_by_version(FakeVersion())  # type: ignore


def test_get_template_by_name_found():
    """Test retrieving template by name."""
    template = get_template_by_name("Tibia 7.4 (Classic)")
    assert template is not None
    assert template == TEMPLATE_7_4


def test_get_template_by_name_not_found():
    """Test get_template_by_name returns None for invalid name."""
    template = get_template_by_name("Nonexistent Template")
    assert template is None


def test_template_immutable():
    """Test that MapTemplate is immutable (frozen dataclass)."""
    with pytest.raises(AttributeError):
        TEMPLATE_7_4.name = "Modified"  # type: ignore


def test_all_templates_have_unique_names():
    """Test all templates have unique names."""
    names = [t.name for t in ALL_TEMPLATES]
    assert len(names) == len(set(names))


def test_all_templates_have_valid_otbm_versions():
    """Test all templates have valid OTBM versions (1-6)."""
    for template in ALL_TEMPLATES:
        assert 1 <= template.otbm_version <= 6


def test_client_id_templates_use_version_5_or_6():
    """Test ClientID templates use OTBM version 5 or 6."""
    for template in ALL_TEMPLATES:
        if template.use_client_ids:
            assert template.otbm_version in (5, 6)


def test_server_id_templates_use_version_1_to_4():
    """Test ServerID templates use OTBM version 1-4."""
    for template in ALL_TEMPLATES:
        if not template.use_client_ids:
            assert 1 <= template.otbm_version <= 4


def test_all_templates_have_descriptions():
    """Test all templates have non-empty descriptions."""
    for template in ALL_TEMPLATES:
        assert len(template.description) > 0
        assert len(template.default_description) > 0


def test_map_size_tuple_behavior():
    """Test MapSize works as a tuple (NamedTuple)."""
    size = MapSize(2048, 2048)
    # Can unpack
    width, height = size
    assert width == 2048
    assert height == 2048

    # Can access by index
    assert size[0] == 2048
    assert size[1] == 2048
