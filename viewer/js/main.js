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
     * Reload snapshot from server.
     */
    async reload() {
        this.ui.showLoading();
        
        try {
            // Clear current scene
            this.sceneBuilder.clear();
            this.labelManager.clearLabels();
            
            // Reload data
            this.snapshot = await this.api.fetchSnapshot();
            this.sceneBuilder.buildFromSnapshot(this.snapshot);
            this.labelManager.createLabels(this.snapshot.nodes);
            this.inputController.setNodeMeshes(
                this.sceneBuilder.getAllNodeMeshes()
            );
            this.ui.updateInfoPanel(this.snapshot.metadata);
            
            this.ui.hideLoading();
            console.log('✓ Snapshot reloaded');
            
        } catch (error) {
            console.error('Failed to reload:', error);
            this.ui.hideLoading();
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
