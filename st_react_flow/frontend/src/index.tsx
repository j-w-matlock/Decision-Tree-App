import React from "react";
import { createRoot } from "react-dom/client";
import { withStreamlitConnection } from "streamlit-component-lib";
import App from "./App";
import "./style.css";

const ConnectedApp = withStreamlitConnection(App);

const root = createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <ConnectedApp />
  </React.StrictMode>
);
