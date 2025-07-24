import os
import streamlit as st
import streamlit.components.v1 as components

# Path to this component folder
_component_dir = os.path.dirname(os.path.abspath(__file__))
_build_dir = os.path.join(_component_dir, "build")

# Diagnostics: print path info
st.write(f"🔍 React Flow Component Path: {_build_dir}")
if not os.path.exists(_build_dir):
    st.error(f"❌ React Flow build directory not found: {_build_dir}")
    st.warning("Please ensure you ran `npm run build` in st_react_flow/frontend and committed the build folder.")
else:
    st.success("✅ React Flow build directory found.")

# Declare the production component
_react_flow_prod = components.declare_component(
    "react_flow_canvas_prod",
    path=_build_dir
)

def react_flow(key: str, value=None, dev: bool = False):
    """
    Streamlit wrapper for the React Flow decision tree component.
    If dev=True, connects to the Vite dev server (localhost:5173).
    Otherwise, uses the compiled assets in st_react_flow/build.
    """
    if dev:
        _react_flow_dev = components.declare_component(
            "react_flow_canvas_dev",
            url="http://localhost:5173"
        )
        return _react_flow_dev(key=key, value=value, default=value or {})
    else:
        return _react_flow_prod(key=key, value=value, default=value or {})
