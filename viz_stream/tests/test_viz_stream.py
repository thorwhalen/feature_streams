"""
Tests for viz_stream package.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from viz_stream import VizConfig, PlotType

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for testing
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def test_viz_config_defaults():
    """Test default configuration."""
    config = VizConfig()
    assert config.plot_type == PlotType.LINE
    assert config.fields == ['value']
    assert config.window_size == 200
    assert config.update_interval == 50


def test_custom_config():
    """Test custom configuration."""
    config = VizConfig(
        plot_type=PlotType.SCATTER,
        fields=['x', 'y', 'z'],
        window_size=100,
        title="Custom Plot"
    )
    assert config.plot_type == PlotType.SCATTER
    assert config.fields == ['x', 'y', 'z']
    assert config.window_size == 100
    assert config.title == "Custom Plot"


def test_plot_type_enum():
    """Test plot type enumeration."""
    assert PlotType.LINE.value == "line"
    assert PlotType.SCATTER.value == "scatter"
    assert PlotType.BAR.value == "bar"


def test_visualizer_creation():
    """Test visualizer creation."""
    if not MATPLOTLIB_AVAILABLE:
        print("⊘ matplotlib not available, skipping visualizer test")
        return

    from viz_stream.core import StreamVisualizer

    config = VizConfig(fields=['x', 'y'])
    viz = StreamVisualizer(config)

    assert viz.config == config
    assert 'x' in viz.data_buffers
    assert 'y' in viz.data_buffers
    print("✓ Visualizer creation OK")


def test_update_data():
    """Test data update."""
    if not MATPLOTLIB_AVAILABLE:
        print("⊘ matplotlib not available, skipping data update test")
        return

    from viz_stream.core import StreamVisualizer

    config = VizConfig(fields=['value'])
    viz = StreamVisualizer(config)

    # Update with test data
    viz.update_data({'timestamp': 1.0, 'value': 10.0})
    viz.update_data({'timestamp': 2.0, 'value': 20.0})

    assert len(viz.data_buffers['value']) == 2
    assert list(viz.data_buffers['value']) == [10.0, 20.0]
    print("✓ Data update OK")


if __name__ == "__main__":
    print("Testing viz config...")
    test_viz_config_defaults()
    print("✓ Config OK")

    print("\nTesting custom config...")
    test_custom_config()
    print("✓ Custom config OK")

    print("\nTesting plot type enum...")
    test_plot_type_enum()
    print("✓ Plot type enum OK")

    print("\nTesting visualizer creation...")
    test_visualizer_creation()

    print("\nTesting data update...")
    test_update_data()

    print("\nAll tests completed!")
