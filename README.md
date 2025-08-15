# 🧠 Mind Map Builder

An interactive Streamlit app for freely creating and organising ideas as a mind map.

## Features

- Visual canvas powered by [`streamlit-drawable-canvas`](https://github.com/andfanilo/streamlit-drawable-canvas)
- Add, edit or delete nodes and edges from the sidebar
- Drag nodes on the canvas to arrange them
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
5. **Drag nodes on the canvas** to reposition them.
6. Use the **Actions** toolbar to export the current map to JSON, import a saved map or clear the canvas.

## Examples and Tutorials

Additional tutorials and sample maps will be added to the repository.

## License

[MIT](LICENSE)

