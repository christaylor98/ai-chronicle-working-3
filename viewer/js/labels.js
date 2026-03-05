/**
 * 2D label overlay system for 3D nodes.
 * Projects 3D positions to screen space.
 */

export class LabelManager {
    constructor(camera, container) {
        this.camera = camera;
        this.container = document.getElementById(container);
        this.labels = new Map();  // nodeId -> DOM element
        this.nodePositions = new Map();  // nodeId -> {x, y, z}
        this.nodeImportance = new Map();  // nodeId -> importance score
        this.nodeMeshes = null;  // Reference to node meshes for visibility
        this.maxLabels = 30;  // LOD: limit number of visible labels
    }

    /**
     * Set reference to node meshes for visibility checking.
     */
    setNodeMeshes(nodeMeshes) {
        this.nodeMeshes = nodeMeshes;
    }

    /**
     * Create labels for all nodes.
     */
    createLabels(nodes) {
        this.clearLabels();
        
        for (const node of nodes) {
            const label = this.createLabel(node);
            this.labels.set(node.id, label);
            this.nodePositions.set(node.id, { x: node.x, y: node.y, z: node.z });
            this.nodeImportance.set(node.id, node.importance || node.degree || 0);
        }
    }

    /**
     * Create a single label DOM element.
     */
    createLabel(node) {
        const labelDiv = document.createElement('div');
        labelDiv.className = 'node-label';
        labelDiv.textContent = node.label;
        labelDiv.style.display = 'none';  // Hidden by default
        
        this.container.appendChild(labelDiv);
        
        return labelDiv;
    }

    /**
     * Update label positions based on 3D -> 2D projection.
     * CONTEXTUAL: Only shows labels for visible nodes, ranked by importance.
     */
    updateLabelPositions() {
        // Get camera frustum for culling
        const frustum = new THREE.Frustum();
        const projScreenMatrix = new THREE.Matrix4();
        projScreenMatrix.multiplyMatrices(
            this.camera.projectionMatrix,
            this.camera.matrixWorldInverse
        );
        frustum.setFromProjectionMatrix(projScreenMatrix);
        
        // Build candidate list: only nodes that are visible (not hidden by telescope)
        const labelCandidates = [];
        for (const [nodeId, pos] of this.nodePositions) {
            const vector = new THREE.Vector3(pos.x, pos.y, pos.z);
            const inFrustum = frustum.containsPoint(vector);
            
            // Check if node mesh is visible (telescope effect)
            const mesh = this.nodeMeshes?.get(nodeId);
            const nodeVisible = mesh ? mesh.visible : true;
            
            // Only consider nodes that are both in frustum AND visible
            if (inFrustum && nodeVisible) {
                const importance = this.nodeImportance.get(nodeId) || 0;
                labelCandidates.push({
                    nodeId,
                    importance,
                    position: vector
                });
            }
        }
        
        // Sort by importance (highest first) and take top N
        labelCandidates.sort((a, b) => b.importance - a.importance);
        const visibleLabels = labelCandidates.slice(0, this.maxLabels);
        
        const visibleIds = new Set(visibleLabels.map(l => l.nodeId));
        
        // Update visible labels
        for (const { nodeId, position } of visibleLabels) {
            const label = this.labels.get(nodeId);
            if (!label) continue;
            
            // Project to screen space
            const screenPos = this.project3DToScreen(position);
            
            if (screenPos) {
                label.style.left = `${screenPos.x}px`;
                label.style.top = `${screenPos.y}px`;
                label.style.display = 'block';
            } else {
                label.style.display = 'none';
            }
        }
        
        // Hide non-visible labels
        for (const [nodeId, label] of this.labels) {
            if (!visibleIds.has(nodeId)) {
                label.style.display = 'none';
            }
        }
    }

    /**
     * Project 3D position to 2D screen coordinates.
     */
    project3DToScreen(position) {
        const vector = position.clone();
        vector.project(this.camera);
        
        // Check if behind camera
        if (vector.z > 1) return null;
        
        const x = (vector.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-vector.y * 0.5 + 0.5) * window.innerHeight;
        
        return { x, y };
    }

    /**
     * Clear all labels.
     */
    clearLabels() {
        for (const label of this.labels.values()) {
            this.container.removeChild(label);
        }
        this.labels.clear();
        this.nodePositions.clear();
        this.nodeImportance.clear();
    }

    /**
     * Show/hide a specific label.
     */
    setLabelVisibility(nodeId, visible) {
        const label = this.labels.get(nodeId);
        if (label) {
            label.style.display = visible ? 'block' : 'none';
        }
    }

    /**
     * Adjust max labels for performance tuning.
     */
    setMaxLabels(count) {
        this.maxLabels = count;
    }
}
