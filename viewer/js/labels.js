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
        this.maxLabels = 30;  // LOD: limit number of visible labels
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
        
        // Calculate distances from camera for LOD
        const labelDistances = [];
        for (const [nodeId, pos] of this.nodePositions) {
            const vector = new THREE.Vector3(pos.x, pos.y, pos.z);
            const distance = this.camera.position.distanceTo(vector);
            const inFrustum = frustum.containsPoint(vector);
            
            labelDistances.push({
                nodeId,
                distance,
                inFrustum,
                position: vector
            });
        }
        
        // Sort by distance and take closest N labels
        labelDistances.sort((a, b) => a.distance - b.distance);
        const visibleLabels = labelDistances
            .filter(l => l.inFrustum)
            .slice(0, this.maxLabels);
        
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
