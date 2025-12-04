import webbrowser
import os
import urllib.parse
import http.server
import socketserver
import threading
from matplotlib.figure import Figure
import pkg_resources
import matplotlib.pyplot as plt
from matplotlib import rc
rc("svg", fonttype='path')
import time
import networkx as nx
import tkinter as tk
import re
from pyvis.network import Network





class MplEditor:

    """
    Browser-based SVG editor for Matplotlib figures.

    This class converts a Matplotlib figure into an SVG file and opens it in a
    custom HTML editor served on a lightweight HTTP server. The editor allows
    interactive manipulation of the SVG image inside a web browser.

    Parameters
    ----------
    figure : matplotlib.figure.Figure
        The Matplotlib figure that will be exported as a temporary SVG file.

    Attributes
    ----------
    figure : matplotlib.figure.Figure
        Input Matplotlib figure.

    _package_path : str
        Absolute path to the package directory used to store temporary files.

    _cwd : str
        Original working directory restored after editing.

    Examples
    --------
    Create a simple plot and edit it in the browser:

    >>> import matplotlib.pyplot as plt
    >>> from editor import MplEditor
    >>> fig, ax = plt.subplots()
    >>> ax.plot([1, 2, 3], [3, 1, 4])
    >>> MplEditor(fig).edit()  # doctest: +SKIP

    Notes
    -----
    - A temporary file ``tmp.svg`` is created inside the package directory.
    - The editor is served on ``http://localhost:8005``.
    - The browser is automatically opened when calling :meth:`edit`.
    """
    
    def __init__(self, figure:Figure):
        
        """
        Initialize an instance of :class:`MplEditor`.

        This constructor stores the input Matplotlib figure, determines the
        package directory used for temporary files, and saves the current
        working directory so that it can be restored after editing.

        Parameters
        ----------
        figure : matplotlib.figure.Figure
            The Matplotlib figure that will be exported as a temporary SVG file.

        Attributes
        ----------
        figure : matplotlib.figure.Figure
            The input Matplotlib figure to be displayed in the browser editor.

        _package_path : str
            Absolute path to the package directory where temporary files are stored.

        _cwd : str
            Original working directory, restored at the end of :meth:`edit`.

        Notes
        -----
        The package directory is obtained using :func:`pkg_resources.resource_filename`.
        """

        self.figure = figure
        def get_package_directory():
            return pkg_resources.resource_filename(__name__, '')
        
        self._package_path = get_package_directory()
        self._cwd = os.getcwd()

        
        

    def save_tmp(self):

        """
        Save the Matplotlib figure as an SVG file named ``tmp.svg``.

        The file is written inside the package directory and overwrites
        any existing version.

        Returns
        -------
        None
        """

        self.figure.savefig(os.path.join(self._package_path, 'tmp.svg'), format='svg', bbox_inches='tight', transparent=True)

        
    
    def run_server(self):
        """
        Start a blocking HTTP server on port 8005.

        The server exposes the package directory so that HTML files and
        the temporary SVG file can be accessed by the browser.

        Notes
        -----
        - This method blocks execution until the process is terminated.
        - Typically it is run in a daemon thread by :meth:`edit`.
        """
        
        os.chdir(self._package_path)
        
        socketserver.TCPServer.allow_reuse_address = True
        handler = http.server.SimpleHTTPRequestHandler
        handler.directory = self._package_path
        httpd = socketserver.TCPServer(("", 8005), handler)
        httpd.serve_forever()
        

       
        
    def open_in_browser(self):
        """
        Open the built-in HTML editor in the system web browser.

        The editor is loaded using ``vecedit.html`` and receives
        the ``tmp.svg`` file via a query parameter.

        Returns
        -------
        None
        """
        os.chdir(self._package_path)

        file_path = 'vecedit.html'
        argument = 'tmp.svg'

        file_path = file_path.replace("\\", "/")
        argument = argument.replace("\\", "/")

        url_with_argument = f"http://localhost:8005/{os.path.basename(file_path)}?graph={urllib.parse.quote(argument)}"

        webbrowser.open(url_with_argument)
    

        

    def del_tmp(self):
        """
        Remove the temporary SVG file if it exists.

        Returns
        -------
        None
        """
        try:
            if os.path.exists(os.path.join(self._package_path, 'tmp.svg')):
                os.remove(os.path.join(self._package_path, 'tmp.svg'))
        except:
            pass
    
    
    def edit(self):
        
        """
        Launch the full browser-based editing workflow.

        Steps
        -----
        1. Save the Matplotlib figure to ``tmp.svg``.
        2. Start the HTTP server in a background thread.
        3. Open the browser with the generated editor.
        4. Restore working directory.

        Returns
        -------
        None
        """

        self.save_tmp()

        server_thread = threading.Thread(target=self.run_server, daemon=True)
        server_thread.start()
        time.sleep(5)
        
        self.open_in_browser()
        
        time.sleep(10)
        
        os.chdir(self._cwd)

        
   

class NxEditor():

    """
    Interactive editor for NetworkX graphs based on pyvis.

    This class generates a temporary HTML file containing a pyvis visualization
    of a NetworkX graph and injects custom JavaScript controls that enable:

    - node selection,
    - node deletion,
    - undo history,
    - physics controls,
    - node size scaling,
    - font size scaling,
    - export to PNG/JPEG/SVG.

    Parameters
    ----------
    network : networkx.Graph
        The NetworkX graph to be visualized and edited.

    Attributes
    ----------
    network : networkx.Graph
        The graph displayed in the editor.

    _package_path : str
        Directory containing temporary files and resources.

    _cwd : str
        Original working directory restored after execution.

    Examples
    --------
    Open an editable visualization of a simple graph:

    >>> import networkx as nx
    >>> from editor import NxEditor
    >>> G = nx.cycle_graph(4)
    >>> NxEditor(G).edit() 

    Notes
    -----
    Editing operations occur only in the browser and do not modify the original
    NetworkX graph object in Python.
    """

    def __init__(self, network:nx.Graph):
        
        """
        Initialize an instance of :class:`NxEditor`.

        This constructor stores the input NetworkX graph, determines the
        package directory for temporary resources, and saves the current
        working directory so it can be restored after the editing session.

        Parameters
        ----------
        network : networkx.Graph
            The NetworkX graph to be displayed and edited in the browser-based
            pyvis interface.

        Attributes
        ----------
        network : networkx.Graph
            The input graph rendered by the editor.

        _package_path : str
            Absolute path to the package directory used to store temporary HTML
            files and related resources.
            
        _cwd : str
            Original working directory, restored after :meth:`edit` completes.

        Notes
        -----
        The package directory path is resolved using
        :func:`pkg_resources.resource_filename`.
        """

        self.network = network
        def get_package_directory():
            return pkg_resources.resource_filename(__name__, '')
        
        self._package_path = get_package_directory()
        self._cwd = os.getcwd()

    def edit(self):
       
        """
        Generate and open an interactive pyvis-based graph editor.

        The editor is created in ``tmp.html`` inside the package directory.
        Custom JavaScript code is injected into the HTML to enable interactive
        editing, exporting, and layout control.

        Returns
        -------
        None
        """
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    
        desired_height = int(screen_height * 0.8)
        desired_width = int(screen_width * 0.99)
    
        net = Network(notebook=True, height=f"{desired_height}px", width=f"{desired_width}px")
        net.from_nx(self.network)
        net.repulsion(node_distance=150, spring_length=200)
    
        file_path = os.path.join(self._package_path, 'tmp.html')
        
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        net.show(file_path)
    

        js_code = """
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

        <script type="text/javascript">
        
            let selectedNodes = [];
            let previousStyles = {}; 
            let undoStack = [];
    
            function saveNetworkState() {
                const nodes = network.body.data.nodes.get();
                const edges = network.body.data.edges.get();
                const styles = {};
            
                nodes.forEach(node => {
                    styles[node.id] = {
                        color: previousStyles[node.id]?.color || node.color || null
                    };
                });
            
                undoStack.push(JSON.stringify({ nodes, edges, styles }));
            }
            
            
            function removeSelectedNodes() {
                if (selectedNodes.length > 0) {
                    saveNetworkState();
            
                    network.body.data.nodes.remove(selectedNodes.map(id => ({ id })));
                    selectedNodes = [];
                } else {
                    alert("No nodes selected.");
                }
            }
            
            function undo() {
                if (undoStack.length > 0) {
                    const previousState = JSON.parse(undoStack.pop());
            
                    network.body.data.nodes.clear();
                    network.body.data.edges.clear();
                    network.body.data.nodes.add(previousState.nodes);
                    network.body.data.edges.add(previousState.edges);
            
                    Object.keys(previousState.styles).forEach(nodeId => {
                        network.body.data.nodes.update({
                            id: nodeId,
                            ...previousState.styles[nodeId]
                        });
                    });
            
                    selectedNodes = [];
                    previousStyles = previousState.styles;
                } else {
                    alert("Nothing to undo.");
                }
            }
            
            network.on("selectNode", function (params) {
                if (event.ctrlKey) {
                    selectedNodes = [...new Set([...selectedNodes, ...params.nodes])];
                } else {
                    selectedNodes.forEach(nodeId => {
                        if (previousStyles[nodeId]) {
                            network.body.data.nodes.update({
                                id: nodeId,
                                ...previousStyles[nodeId]
                            });
                        }
                    });
                    selectedNodes = params.nodes;
                }
            
                params.nodes.forEach(nodeId => {
                    const nodeData = network.body.data.nodes.get(nodeId);
                    if (!previousStyles[nodeId]) {
                        previousStyles[nodeId] = {
                            color: nodeData.color || null
                        };
                    }
                    network.body.data.nodes.update({
                        id: nodeId,
                        color: "black"
                    });
                });
            });
            
            network.on("deselectNode", function (params) {
                if (!event.ctrlKey) {
                    selectedNodes.forEach(nodeId => {
                        if (previousStyles[nodeId]) {
                            network.body.data.nodes.update({
                                id: nodeId,
                                ...previousStyles[nodeId]
                            });
                        }
                    });
                    selectedNodes = [];
                } else {
                    params.nodes.forEach(nodeId => {
                        if (previousStyles[nodeId]) {
                            network.body.data.nodes.update({
                                id: nodeId,
                                ...previousStyles[nodeId]
                            });
                        }
                    });
                }
            });
                    
                    
            
            
            
            function changePhysics(value) {
                network.setOptions({
                    physics: {
                        solver: 'repulsion',
                        repulsion: {
                            nodeDistance: parseInt(value),
                        },
                    },
                });
            }
            
            
            
            
            
                            
            let originalNodeSizes = {};
            
            function initializeOriginalNodeSizes() {
                network.body.data.nodes.get().forEach(node => {
                    if (!originalNodeSizes[node.id]) {
                        originalNodeSizes[node.id] = node.size || 1; 
                    }
                });
            }
            
            function scaleNetworkSize(scaleFactor) {
                initializeOriginalNodeSizes(); 
            
                network.body.data.nodes.update(
                    network.body.data.nodes.get().map(node => ({
                        id: node.id,
                        size: originalNodeSizes[node.id] * scaleFactor 
                    }))
                );
            }
                            
                        
            
            function changeFontSize(size) {
                network.body.data.nodes.update(
                    network.body.data.nodes.get().map(node => ({
                        id: node.id,
                        font: { size: size }
                    }))
                );
            }
            
            
            let physicsEnabled = true;
            
            function togglePhysics() {
                physicsEnabled = !physicsEnabled;
            
                network.setOptions({
                    physics: physicsEnabled
                });
            

                document.getElementById("togglePhysicsButton").innerText = physicsEnabled
                    ? "Disable Physics"
                    : "Enable Physics";
            }



            function downloadFile(blob, filename) {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = filename;
                link.click();
    
                URL.revokeObjectURL(link.href);
            }


            function saveGraph(format, resolution = 96) {
                
                if (format === "svg") {

                    const positions = network.getPositions();

                    const nodes = network.body.data.nodes.get();
                    const edges = network.body.data.edges.get();
                
                    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                    Object.values(positions).forEach(pos => {
                        minX = Math.min(minX, pos.x);
                        maxX = Math.max(maxX, pos.x);
                        minY = Math.min(minY, pos.y);
                        maxY = Math.max(maxY, pos.y);
                    });
                
                    const margin = 600; 
                    const width = maxX - minX + margin * 2.5; 
                    const height = maxY - minY + margin * 1.5; 
                
                    const offsetX = margin - minX; 
                    const offsetY = margin - minY; 
                
                    let svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">`;
                
                    edges.forEach((edge) => {
                        const from = positions[edge.from];
                        const to = positions[edge.to];
                        if (from && to) {
                            const controlX = (from.x + to.x) / 2; 
                            const controlY = (from.y + to.y) / 2 - 50; 
                    
                            const pathData = `M${from.x + offsetX},${from.y + offsetY} C${controlX + offsetX},${controlY + offsetY} ${controlX + offsetX},${controlY + offsetY} ${to.x + offsetX},${to.y + offsetY}`;
                            const color = edge.color || "black"; 
                            const width = edge.width || 2; 
                            svgContent += `<path d="${pathData}" stroke="${color}" stroke-width="${width}" fill="none"/>`;
                        }
                    });
                

                    nodes.forEach((node) => {
                        const pos = positions[node.id];
                        if (pos) {
                            const size = (node.size || 10); 
                            const color = node.color || "blue"; 
                            svgContent += `<circle cx="${pos.x + offsetX}" cy="${pos.y + offsetY}" r="${size}" fill="${color}" />`;
                
                            const labelColor = node.font?.color || "black"; 
                            const labelFontSize = node.font?.size || 12; 
                            svgContent += `<text x="${pos.x + offsetX + size + 5}" y="${pos.y + offsetY}" font-size="${labelFontSize}" fill="${labelColor}">${node.label || node.id}</text>`;
                        }
                    });
                
                    svgContent += `</svg>`;
                
                    const blob = new Blob([svgContent], { type: "image/svg+xml;charset=utf-8" });
                    const link = document.createElement("a");
                    link.href = URL.createObjectURL(blob);
                    link.download = "graph.svg";
                    link.click();
                                            
                    
                } else {
                    
                    const positions = network.getPositions();

                    const nodes = network.body.data.nodes.get();
                    const edges = network.body.data.edges.get();
                
                    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                    Object.values(positions).forEach(pos => {
                        minX = Math.min(minX, pos.x);
                        maxX = Math.max(maxX, pos.x);
                        minY = Math.min(minY, pos.y);
                        maxY = Math.max(maxY, pos.y);
                    });
                
                    const margin = 600;  
                    const width = maxX - minX + margin * 2.5; 
                    const height = maxY - minY + margin * 1.5; 
                
                    const offsetX = margin - minX; 
                    const offsetY = margin - minY; 
                
                    let svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">`;
                
                    edges.forEach((edge) => {
                        const from = positions[edge.from];
                        const to = positions[edge.to];
                        if (from && to) {
                            const controlX = (from.x + to.x) / 2; 
                            const controlY = (from.y + to.y) / 2 - 50; 
                    
                            const pathData = `M${from.x + offsetX},${from.y + offsetY} C${controlX + offsetX},${controlY + offsetY} ${controlX + offsetX},${controlY + offsetY} ${to.x + offsetX},${to.y + offsetY}`;
                            const color = edge.color || "black"; 
                            const width = edge.width || 2; 
                            svgContent += `<path d="${pathData}" stroke="${color}" stroke-width="${width}" fill="none"/>`;
                        }
                    });
                
                    nodes.forEach((node) => {
                        const pos = positions[node.id];
                        if (pos) {
                            const size = (node.size || 10); 
                            const color = node.color || "blue"; 
                            svgContent += `<circle cx="${pos.x + offsetX}" cy="${pos.y + offsetY}" r="${size}" fill="${color}" />`;
                
                            const labelColor = node.font?.color || "black"; 
                            const labelFontSize = node.font?.size || 12; 
                            svgContent += `<text x="${pos.x + offsetX + size + 5}" y="${pos.y + offsetY}" font-size="${labelFontSize}" fill="${labelColor}">${node.label || node.id}</text>`;
                        }
                    });
                
                    svgContent += `</svg>`;
                    
                    const svgBlob = new Blob([svgContent], { type: 'image/svg+xml' });
                    const svgUrl = URL.createObjectURL(svgBlob);
                    
                    const getScaleFactor = (resolution = 300) => {
                        const defaultDPI = 96;
                        return resolution / defaultDPI;
                    };
                    
                    const scaleFactor = getScaleFactor(resolution || 300);
                    
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    const img = new Image();
                    
                    img.onload = () => {
                        try {
                            canvas.width = width * scaleFactor;
                            canvas.height = height * scaleFactor;
                    
                            context.setTransform(scaleFactor, 0, 0, scaleFactor, 0, 0);
                    
                            if (format === 'jpeg' || format === 'jpg') {
                                context.fillStyle = 'white';
                                context.fillRect(0, 0, canvas.width, canvas.height);
                            }
                    
                            context.drawImage(img, 0, 0, width, height);
                    
                            canvas.toBlob((blob) => {
                                if (blob) {
                                    downloadFile(blob, `image.${format}`);
                                } else {
                                    console.error('Błąd: Blob jest pusty!');
                                }
                            }, `image/${format}`);
                        } catch (error) {
                            console.error('Błąd podczas rysowania na canvasie:', error);
                        }
                    };
                    
                    img.onerror = (error) => {
                        console.error('Nie udało się załadować obrazu SVG jako źródła:', error);
                    };
                    
                    img.src = svgUrl;
                    

                        
                        
                }
            }
                        
                        
                        
    
    
            document.body.insertAdjacentHTML('beforeend', `
                <div style="position: fixed; top: 0; left: 0; width: 100%; background: #353834; padding: 10px; z-index: 1000; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid #ddd;">
                    <button onclick="removeSelectedNodes()">
                        <i class="fa-solid fa-eraser"></i>
                    </button>
                    
                    

                    
                    
                    <button onclick="undo()">
                        <i class="fa-solid fa-arrow-left"></i>
                    </button>
                    

                    <label for="formatSelect" style="color: white;">Save As:</label>
                    <select id="formatSelect">
                        <option value="png">PNG</option>
                        <option value="jpg">JPEG</option>
                        <option value="svg">SVG</option>

                    </select>
                    
                    <label for="resolutionSelect" style="color: white;">Resolution (DPI):</label>
                    <select id="resolutionSelect">
                        <option value="200">300 DPI</option>
                        <option value="300">300 DPI</option>
                        <option value="600">600 DPI</option>

                    </select>
                    
                    <button onclick="saveGraph(
                        document.getElementById('formatSelect').value,
                        parseInt(document.getElementById('resolutionSelect').value)
                    )">
                        Export Graph
                    </button>
                    

        
                    <label style="color: white;">Font Size:</label>
                    <input type="range" min="10" max="50" value="14" onchange="changeFontSize(this.value)">
                    <label style="color: white;">Node Size:</label>
                    <input type="range" min="0.1" max="10" value="0.1" onchange="scaleNetworkSize(this.value)">
                    
                    <button id="togglePhysicsButton" onclick="togglePhysics()">Disable Physics</button>

                    <label style="color: white;">Physics:</label>
                    <input type="range" min="50" max="500" value="200" step="10" onchange="changePhysics(this.value)">
               
                </div>
            `);
        </script>
        """

        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
            
        font_awesome_link = '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">'
        html_content = re.sub(r"(<head>)", r"\1\n" + font_awesome_link, html_content, flags=re.IGNORECASE)
        
        modified_html = re.sub(r"(</body>)", js_code + "</body>", html_content, flags=re.IGNORECASE)

    
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(modified_html)
    
        webbrowser.open(file_path)
        
        
        
        

       