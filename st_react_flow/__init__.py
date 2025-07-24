import os
import json
import streamlit as st
import streamlit.components.v1 as components

# Folder of this file
_component_dir = os.path.dirname(os.path.abspath(__file__))

# In prod, React build is at st_react_flow/build
_build_dir = os.path.join(_component_dir, "build")

# Declare component for prod bundle
_react_flow_prod = components.declare_component(
    "react_flow_canvas_prod",
    path=_build_dir
)

def react_flow(key: str, value=None, dev: bool = False):
    """
    Streamlit wrapper. If dev=True, expects Vite dev server running at :5173.
    Otherwise serves the bundled build in st_react_flow/build.
    """
    if dev:
        # Connect to dev server
        _react_flow_dev = components.declare_component(
            "react_flow_canvas_dev",
            url="http://localhost:5173"
        )
        data = _react_flow_dev(key=key, value=value, default=value or {})
    else:
        data = _react_flow_prod(key=key, value=value, default=value or {})

    return data
