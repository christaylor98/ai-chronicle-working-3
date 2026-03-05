"""
Flask server for 3D projection visualization.
Serves static files and provides API for snapshot data.
"""

from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
import json
import sys
import mimetypes

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.visualization.snapshot_adapter_3d import ProjectionSnapshot3DAdapter

# Ensure JavaScript files are served with correct MIME type for ES6 modules
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')


class Viewer3DServer:
    """
    Lightweight HTTP server for 3D projection visualization.
    Provides API endpoints and serves static viewer files.
    """
    
    def __init__(self, projection_path: str, host: str = "127.0.0.1", port: int = 8000):
        """Initialize server with projection data."""
        self.projection_path = Path(projection_path)
        self.host = host
        self.port = port
        
        # Create Flask app
        self.app = Flask(__name__, 
                        static_folder=str(Path(__file__).parent.parent.parent / "viewer"),
                        static_url_path="")
        
        # Initialize adapter
        self.adapter = ProjectionSnapshot3DAdapter(str(self.projection_path))
        self.snapshot_cache = None
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register Flask routes."""
        
        @self.app.route("/")
        def index():
            """Serve main HTML page."""
            return send_from_directory(self.app.static_folder, "index.html")
        
        @self.app.route("/api/snapshot")
        def get_snapshot():
            """Get 3D snapshot data."""
            if self.snapshot_cache is None:
                snapshot = self.adapter.convert_to_snapshot()
                self.snapshot_cache = {
                    "nodes": snapshot.nodes,
                    "edges": snapshot.edges,
                    "metadata": snapshot.metadata
                }
            return jsonify(self.snapshot_cache)
        
        @self.app.route("/api/snapshot/reload")
        def reload_snapshot():
            """Force reload of snapshot data."""
            self.snapshot_cache = None
            self.adapter = ProjectionSnapshot3DAdapter(str(self.projection_path))
            return jsonify({"status": "reloaded"})
        
        @self.app.route("/api/health")
        def health():
            """Health check endpoint."""
            return jsonify({
                "status": "ok",
                "projection_file": str(self.projection_path),
                "projection_exists": self.projection_path.exists()
            })
        
        @self.app.route("/api/node/<node_id>")
        def get_node_details(node_id):
            """Get detailed information about a specific node."""
            # Load original projection data
            with open(self.projection_path, 'r') as f:
                projection = json.load(f)
            
            # Find node
            for node in projection.get("nodes", []):
                if node["node_id"] == node_id:
                    return jsonify(node)
            
            return jsonify({"error": "Node not found"}), 404
        
        @self.app.route("/api/edge/<source_id>/<target_id>")
        def get_edge_details(source_id, target_id):
            """Get detailed information about a specific edge."""
            # Load original projection data
            with open(self.projection_path, 'r') as f:
                projection = json.load(f)
            
            # Find edge (check both directions)
            for edge in projection.get("edges", []):
                if (edge["source"] == source_id and edge["target"] == target_id) or \
                   (edge["source"] == target_id and edge["target"] == source_id):
                    return jsonify(edge)
            
            return jsonify({"error": "Edge not found"}), 404
    
    def run(self):
        """Start the Flask development server."""
        print(f"\n{'='*60}")
        print(f"🚀 3D Projection Viewer")
        print(f"{'='*60}")
        print(f"Projection: {self.projection_path.name}")
        print(f"URL:        http://{self.host}:{self.port}")
        print(f"API:        http://{self.host}:{self.port}/api/snapshot")
        print(f"{'='*60}\n")
        
        self.app.run(host=self.host, port=self.port, debug=True)


def run_viewer_server(projection_path: str, host: str = "127.0.0.1", port: int = 8000):
    """
    Launch 3D visualization server for a projection file.
    
    Args:
        projection_path: Path to projection JSON file
        host: Server host address
        port: Server port number
    """
    server = Viewer3DServer(projection_path, host, port)
    server.run()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python server_3d.py <projection.json> [port]")
        print("\nExample:")
        print("  python server_3d.py projections/projection_1_t0.2_d1.json 8000")
        sys.exit(1)
    
    projection_file = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    run_viewer_server(projection_file, port=port)
