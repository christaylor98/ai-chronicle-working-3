/**
 * Main application orchestrator.
 * Initializes all systems and manages application lifecycle.
 */

import { API } from './api.js';
import { Renderer } from './renderer.js';
import { SceneBuilder } from './scene.js';
import { InputController } from './input.js';
import { LabelManager } from './labels.js';
import { UI } from './ui.js';


class ProjectionViewer3D {
    constructor() {
        // Initialize subsystems
        this.api = new API();
        this.ui = new UI();
        this.renderer = new Renderer('main-canvas');
        this.sceneBuilder = new SceneBuilder(this.renderer.getScene());
        this.inputController = new InputController(
            this.renderer.getCamera(),
            this.renderer.renderer.domElement
        );
        this.labelManager = new LabelManager(
            this.renderer.getCamera(),
            'labels-container'
        );
        
        // Application state
        this.snapshot = null;
        this.selectedNodeId = null;
        this.nodeScaleFactor = 1.0;
        this.initialCameraPosition = { x: 15, y: 15, z: 15 };
        
        // Initialize
        this.init();
    }

    async init() {
        try {
            this.ui.showLoading();
            
            // Load snapshot from API
            console.log('Fetching snapshot data...');
            this.snapshot = await this.api.fetchSnapshot();
            console.log('Snapshot loaded:', this.snapshot.metadata);
            
            // Build 3D scene
            console.log('Building 3D scene...');
            this.sceneBuilder.buildFromSnapshot(this.snapshot);
            
            // Create labels
            console.log('Creating labels...');
            this.labelManager.createLabels(this.snapshot.nodes);
            
            // Setup input handling
            this.inputController.setNodeMeshes(
                this.sceneBuilder.getAllNodeMeshes()
            );
            this.inputController.setNodeClickCallback((nodeData) => {
                this.onNodeClick(nodeData);
            });
            
            // Update UI with metadata
            this.ui.updateInfoPanel(this.snapshot.metadata);
            
            // Setup view controls
            this.ui.setupViewControls({
                onLODChange: (value) => this.setLabelLOD(value),
                onNodeScaleChange: (scale) => this.setNodeScale(scale)
            });
            
            // Start render loop
            this.renderer.startAnimationLoop(() => this.update());
            
            this.ui.hideLoading();
            console.log('✓ Viewer ready');
            
        } catch (error) {
            console.error('Failed to initialize viewer:', error);
            this.ui.hideLoading();
            this.ui.showError(`Failed to load projection: ${error.message}`);
        }
    }

    /**
     * Animation loop update callback.
     */
    update() {
        // Update label positions every frame
        this.labelManager.updateLabelPositions();
    }

    /**
     * Handle node click events.
     */
    async onNodeClick(nodeData) {
        const nodeId = nodeData.nodeId;
        
        // Unhighlight previous selection
        if (this.selectedNodeId) {
            this.sceneBuilder.highlightNode(this.selectedNodeId, false);
        }
        
        // Highlight new selection
        this.selectedNodeId = nodeId;
        this.sceneBuilder.highlightNode(nodeId, true);
        
        // Fetch full node details from API
        try {
            const fullNodeData = await this.api.fetchNodeDetails(nodeId);
            this.ui.showNodeDetails(nodeData, fullNodeData);
        } catch (error) {
            console.warn('Failed to fetch node details:', error);
            this.ui.showNodeDetails(nodeData, null);
        }
    }

    /**
     * Get current snapshot metadata.
     */
    getMetadata() {
        return this.snapshot?.metadata;
    }

    /**
     * Set label LOD (level of detail).
     */
    setLabelLOD(maxLabels) {
        this.labelManager.setMaxLabels(maxLabels);
        console.log(`Label LOD set to ${maxLabels}`);
    }

    /**
     * Set node scale factor.
     */
    setNodeScale(scale) {
        this.nodeScaleFactor = scale;
        
        // Update all node meshes
        for (const [nodeId, mesh] of this.sceneBuilder.nodeMeshes) {
            const nodeData = this.sceneBuilder.getNodeData(nodeId);
            if (nodeData) {
                const baseSize = nodeData.size;
                const newScale = baseSize * scale;
                mesh.scale.set(newScale, newScale, newScale);
            }
        }
        
        console.log(`Node scale set to ${(scale * 100).toFixed(0)}%`);
    }

    /**
     * Reset camera to initial position.
     */
    resetCamera() {
        this.renderer.getCamera().position.set(
            this.initialCameraPosition.x,
            this.initialCameraPosition.y,
            this.initialCameraPosition.z
        );
        this.renderer.getCamera().lookAt(0, 0, 0);
        console.log('✓ Camera reset');
    }

    /**
     * Reload snapshot from server.
     */
    async reload() {
        this.ui.showLoading();
        this.ui.setRefreshEnabled(false);
        
        try {
            // Request server to reload projection
            await fetch('/api/snapshot/reload');
            
            // Clear current scene
            this.sceneBuilder.clear();
            this.labelManager.clearLabels();
            
            // Reload data
            this.snapshot = await this.api.fetchSnapshot();
            this.sceneBuilder.buildFromSnapshot(this.snapshot);
            
            // Apply current node scale
            if (this.nodeScaleFactor !== 1.0) {
                this.setNodeScale(this.nodeScaleFactor);
            }
            
            this.labelManager.createLabels(this.snapshot.nodes);
            this.inputController.setNodeMeshes(
                this.sceneBuilder.getAllNodeMeshes()
            );
            this.ui.updateInfoPanel(this.snapshot.metadata);
            
            this.ui.hideLoading();
            this.ui.setRefreshEnabled(true);
            console.log('✓ Snapshot reloaded');
            
        } catch (error) {
            console.error('Failed to reload:', error);
            this.ui.hideLoading();
            this.ui.setRefreshEnabled(true);
            this.ui.showError(`Reload failed: ${error.message}`);
        }
    }
}


// Application entry point
window.addEventListener('DOMContentLoaded', () => {
    console.log('Starting 3D Projection Viewer...');
    window.viewer = new ProjectionViewer3D();
});


// Export for external access
export default ProjectionViewer3D;
