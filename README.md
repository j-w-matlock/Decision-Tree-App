# 🌳 Decision Tree Builder

An interactive Streamlit app for creating and analysing decision trees from left to right.

## Features

- Visual canvas for building decision trees
- Add, edit and delete nodes (decision, chance, outcome and utility)
- Connect nodes with labelled edges and optional probabilities; edit or remove edges
- Automatically distribute probabilities across outgoing edges of chance nodes
- Export or import the tree structure as JSON
- Display decision pathways with their cumulative probabilities, costs, benefits and payoffs
- Export the canvas as a PNG image

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

1. **Add nodes** in the sidebar by providing a label and node type.
2. **Edit or delete nodes** via the *Edit Node* sidebar section. Deleting a node also removes its connected edges.
3. **Add edges** between nodes with optional labels and probabilities.
4. **Edit or delete edges** in the *Edit Edge* sidebar section.
5. Use the **Actions** toolbar to export the current tree to JSON, import a saved tree, clear the canvas or auto-compute probabilities for chance nodes.
6. The **Decision Pathways** table lists each path from root to leaf with its cumulative probability, cost, benefit and payoff.
7. Click **Export PNG** on the canvas to download an image of the current tree.

## Examples and Tutorials

An example JSON file is provided at [`examples/basic_tree.json`](examples/basic_tree.json).
Additional tutorials and sample trees will be added to the repository.

## License

[MIT](LICENSE)

