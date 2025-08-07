import logging
import os
import streamlit as st
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

_component_dir = os.path.dirname(os.path.abspath(__file__))
_build_dir = os.path.join(_component_dir, "build")

if not os.path.exists(_build_dir):
    raise FileNotFoundError(f"React Flow build directory not found: {_build_dir}")

_react_flow_prod = components.declare_component(
    "react_flow_canvas_prod",
    path=_build_dir,
)

def react_flow(key: str, value=None, dev: bool = False, debug: bool = False):
    """Render the React Flow decision tree component.

    Parameters
    ----------
    key:
        Unique Streamlit key for the component instance.
    value:
        Initial graph dictionary passed to the component.
    dev:
        When ``True`` connects to the Vite dev server on ``localhost:5173``.
    debug:
        When ``True`` prints diagnostic information to the Streamlit app.
    """
    if debug:
        st.write(f"React Flow component path: {_build_dir}")

    if dev:
        _react_flow_dev = components.declare_component(
            "react_flow_canvas_dev",
            url="http://localhost:5173",
        )
        return _react_flow_dev(key=key, value=value, default=value or {})
    else:
        return _react_flow_prod(key=key, value=value, default=value or {})

