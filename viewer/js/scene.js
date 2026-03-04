/**
 * 3D scene construction from snapshot data.
 * Creates nodes (spheres) and edges (lines) with visual encodings.
 */

export class SceneBuilder {
    constructor(scene) {
        this.scene = scene;
        this.nodeMeshes = new Map();  // node_id -> mesh
        this.edgeLines = [];
        this.nodeData = new Map();    // node_id -> data
        this.nodeLODEnabled = true;
        this.lodDistanceScale = 1.0;  // Multiplier for LOD distance calculations
    }

    /**
     * Build complete 3D scene from snapshot data.
     */
    buildFromSnapshot(snapshot) {
        this.clear();
        
        const nodes = snapshot.nodes;
        const edges = snapshot.edges;
        
        // Create nodes
        for (const node of nodes) {
            this.createNode(node);
        }
        
        // Create edges
        for (const edge of edges) {
            this.createEdge(edge, nodes);
        }
        
        return {
            nodeMeshes: this.nodeMeshes,
            edgeLines: this.edgeLines
        };
    }

    /**
     * Create a 3D sphere node with visual encoding.
     */
    createNode(nodeData) {
        const { id, x, y, z, size, color, degree } = nodeData;
        
        // Sphere geometry
        const geometry = new THREE.SphereGeometry(size, 32, 32);
        
        // Material with emissive glow based on degree (hub detection)
        const emissiveIntensity = Math.min(degree / 20.0, 0.5);
        const material = new THREE.MeshPhongMaterial({
            color: new THREE.Color(color),
            emissive: new THREE.Color(color),
            emissiveIntensity: emissiveIntensity,
            shininess: 60,
            transparent: false
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(x, y, z);
        
        // Store reference for raycasting
        mesh.userData = {
            nodeId: id,
            nodeData: nodeData
        };
        
        this.scene.add(mesh);
        this.nodeMeshes.set(id, mesh);
        this.nodeData.set(id, nodeData);
    }

    /**
     * Create edge line between two nodes.
     */
    createEdge(edgeData, nodes) {
        const { source, target, weight, type, color } = edgeData;
        
        const sourceNode = this.nodeData.get(source);
        const targetNode = this.nodeData.get(target);
        
        if (!sourceNode || !targetNode) {
            console.warn(`Edge references missing node: ${source} -> ${target}`);
            return;
        }
        
        // Line geometry
        const points = [
            new THREE.Vector3(sourceNode.x, sourceNode.y, sourceNode.z),
            new THREE.Vector3(targetNode.x, targetNode.y, targetNode.z)
        ];
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        // Material with opacity based on weight
        const opacity = Math.max(0.2, Math.min(1.0, weight));
        const material = new THREE.LineBasicMaterial({
            color: new THREE.Color(color),
            opacity: opacity,
            transparent: true,
            linewidth: 1  // Note: linewidth > 1 not supported in WebGL
        });
        
        const line = new THREE.Line(geometry, material);
        line.userData = {
            edgeType: type,
            weight: weight,
            sourceId: source,
            targetId: target
        };
        
        this.scene.add(line);
        this.edgeLines.push(line);
    }

    /**
     * Clear all scene objects.
     */
    clear() {
        // Remove nodes
        for (const mesh of this.nodeMeshes.values()) {
            this.scene.remove(mesh);
            mesh.geometry.dispose();
            mesh.material.dispose();
        }
        this.nodeMeshes.clear();
        this.nodeData.clear();
        
        // Remove edges
        for (const line of this.edgeLines) {
            this.scene.remove(line);
            line.geometry.dispose();
            line.material.dispose();
        }
        this.edgeLines = [];
    }

    /**
     * Get node mesh by ID.
     */
    getNodeMesh(nodeId) {
        return this.nodeMeshes.get(nodeId);
    }

    /**
     * Get node data by ID.
     */
    getNodeData(nodeId) {
        return this.nodeData.get(nodeId);
    }

    /**
     * Get all node meshes for raycasting.
     */
    getAllNodeMeshes() {
        return Array.from(this.nodeMeshes.values());
    }

    /**
     * Highlight a node (e.g., on hover or selection).
     */
    highlightNode(nodeId, highlight = true) {
        const mesh = this.nodeMeshes.get(nodeId);
        if (!mesh) return;
        
        if (highlight) {
            mesh.material.emissiveIntensity = 0.8;
            // Get current base scale from userData if it exists
            const baseScale = mesh.userData.baseScale || 1.0;
            mesh.scale.set(baseScale * 1.2, baseScale * 1.2, baseScale * 1.2);
        } else {
            const nodeData = this.nodeData.get(nodeId);
            const degree = nodeData ? nodeData.degree : 0;
            mesh.material.emissiveIntensity = Math.min(degree / 20.0, 0.5);
            const baseScale = mesh.userData.baseScale || 1.0;
            mesh.scale.set(baseScale, baseScale, baseScale);
        }
    }

    /**
     * Update node scales globally.
     */
    updateNodeScales(scaleFactor) {
        for (const [nodeId, mesh] of this.nodeMeshes) {
            mesh.userData.baseScale = scaleFactor;
            mesh.scale.set(scaleFactor, scaleFactor, scaleFactor);
        }
    }

    /**
     * Update node visibility based on camera distance (telescope effect).
     */
    updateNodeLOD(camera) {
        if (!this.nodeLODEnabled) {
            // Ensure all nodes are visible if LOD disabled
            for (const mesh of this.nodeMeshes.values()) {
                mesh.visible = true;
            }
            return;
        }

        const cameraDistance = camera.position.length();
        
        // Calculate node importance statistics for dynamic thresholds
        const importanceScores = Array.from(this.nodeData.values())
            .map(n => n.importance || n.degree);
        const maxImportance = Math.max(...importanceScores);
        const minImportance = Math.min(...importanceScores);
        const importanceRange = maxImportance - minImportance;
        
        // LOD levels based on camera distance
        const baseLOD = this.lodDistanceScale;
        let visibilityThreshold;
        let visibleCount = 0;
        
        // Dynamic thresholds based on actual importance distribution
        if (cameraDistance < 25 * baseLOD) {
            // Close zoom: show all nodes
            visibilityThreshold = minImportance;
        } else if (cameraDistance < 50 * baseLOD) {
            // Medium zoom: show top 75% by importance
            visibilityThreshold = minImportance + importanceRange * 0.25;
        } else if (cameraDistance < 100 * baseLOD) {
            // Far zoom: show top 50% by importance
            visibilityThreshold = minImportance + importanceRange * 0.5;
        } else if (cameraDistance < 150 * baseLOD) {
            // Very far: show top 25% by importance
            visibilityThreshold = minImportance + importanceRange * 0.75;
        } else {
            // Extreme distance: only show highest importance nodes
            visibilityThreshold = maxImportance - 0.5;
        }
        
        // Apply visibility based on node importance
        for (const [nodeId, mesh] of this.nodeMeshes) {
            const nodeData = this.nodeData.get(nodeId);
            if (nodeData) {
                const importance = nodeData.importance || nodeData.degree;
                const isVisible = importance >= visibilityThreshold;
                mesh.visible = isVisible;
                if (isVisible) visibleCount++;
            }
        }
        
        // Update edge visibility based on connected nodes
        for (const edge of this.edgeLines) {
            const sourceId = edge.userData.sourceId;
            const targetId = edge.userData.targetId;
            const sourceMesh = this.nodeMeshes.get(sourceId);
            const targetMesh = this.nodeMeshes.get(targetId);
            
            // Edge visible only if both nodes are visible
            edge.visible = (sourceMesh?.visible && targetMesh?.visible) || false;
        }
        
        // Log for debugging (throttled)
        if (!this._lastLogTime || Date.now() - this._lastLogTime > 1000) {
            console.log(`Telescope: distance=${cameraDistance.toFixed(1)}, threshold=${visibilityThreshold.toFixed(2)}, visible=${visibleCount}/${this.nodeMeshes.size}`);
            this._lastLogTime = Date.now();
        }
    }

    /**
     * Set LOD distance scale factor.
     */
    setLODDistanceScale(scale) {
        this.lodDistanceScale = scale;
    }

    /**
     * Enable or disable node LOD.
     */
    setNodeLODEnabled(enabled) {
        this.nodeLODEnabled = enabled;
        if (!enabled) {
            // Make all nodes visible
            for (const mesh of this.nodeMeshes.values()) {
                mesh.visible = true;
            }
            for (const edge of this.edgeLines) {
                edge.visible = true;
            }
        }
    }
}
