# 🧠 Mind Map Builder

An interactive Streamlit app for freely creating and organising ideas as a mind map.

## Features

- Visual canvas powered by React Flow with an optional [`streamlit-agraph`](https://github.com/ChrisDelClea/streamlit-agraph) renderer
- Add, edit or delete nodes and edges from the sidebar
- Drag nodes on the React Flow canvas to arrange them without losing their position
- Edges can be color-coded and are drawn with thicker lines for visibility
- Export or import the map structure as JSON

## Setup

1. Install the requirements

   ```bash
   pip install -r requirements.txt
   ```

2. Run the app

   ```bash
   streamlit run streamlit_app.py
   ```

## Using the App

1. **Add nodes** via the *Add Node* sidebar section.
2. **Edit or delete nodes** via the *Edit Node* sidebar section. Deleting a node also removes its connected edges.
3. **Add edges** between nodes using the sidebar and optionally provide a label.
4. **Edit or delete edges** in the *Edit Edge* sidebar section.
5. Choose the canvas engine in the *Canvas Settings* sidebar section. React Flow supports drag-and-drop positioning, while the Agraph option is read-only and relies on automatic layout.
6. Use the **Actions** toolbar to export the current map to JSON, import a saved map or clear the canvas.

### Limitations

- The Agraph renderer is experimental and does not currently allow manual node positioning. Editing still occurs through the sidebar forms.

## Examples and Tutorials

Additional tutorials and sample maps will be added to the repository.

## License

[MIT](LICENSE)

