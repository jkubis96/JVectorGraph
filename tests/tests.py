import os

import matplotlib.pyplot as plt
import networkx as nx
import pytest

from JVG import JVG


def test_mpl_editor_initialization():
    fig, ax = plt.subplots()
    editor = JVG.MplEditor(fig)

    assert editor.figure is fig
    assert os.path.isdir(editor._package_path)
    assert isinstance(editor._cwd, str)


def test_nx_editor_initialization():
    G = nx.path_graph(5)

    sizes = [300, 500, 800, 500, 300]

    nx.draw(G, with_labels=True, node_size=sizes)

    editor = JVG.NxEditor(G)

    assert editor.network is G
    assert os.path.isdir(editor._package_path)
    assert isinstance(editor._cwd, str)
