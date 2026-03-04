/**
 * UI panel management for info display and node details.
 */

export class UI {
    constructor() {
        this.infoPanelElements = {
            focus: document.getElementById('info-focus'),
            threshold: document.getElementById('info-threshold'),
            depth: document.getElementById('info-depth'),
            nodes: document.getElementById('info-nodes'),
            edges: document.getElementById('info-edges'),
            maxDegree: document.getElementById('info-max-degree')
        };
        
        this.detailsPanel = document.getElementById('details-panel');
        this.detailsTitle = document.getElementById('details-title');
        this.detailsContent = document.getElementById('details-content');
        
        this.loadingPanel = document.getElementById('loading');
        
        // View controls
        this.lodSlider = document.getElementById('lod-slider');
        this.lodValue = document.getElementById('lod-value');
        this.nodeScaleSlider = document.getElementById('node-scale-slider');
        this.nodeScaleValue = document.getElementById('node-scale-value');
        this.refreshBtn = document.getElementById('refresh-btn');
        this.resetCameraBtn = document.getElementById('reset-camera-btn');
        
        // Make closeDetails available globally for HTML onclick
        window.UI = this;
    }

    /**
     * Update info panel with snapshot metadata.
     */
    updateInfoPanel(metadata) {
        const params = metadata.projection_parameters || {};
        
        this.infoPanelElements.focus.textContent = this.truncate(params.focus_node || '-', 16);
        this.infoPanelElements.threshold.textContent = params.coherence_threshold || '-';
        this.infoPanelElements.depth.textContent = params.max_depth || '-';
        this.infoPanelElements.nodes.textContent = metadata.node_count || '-';
        this.infoPanelElements.edges.textContent = metadata.edge_count || '-';
        this.infoPanelElements.maxDegree.textContent = metadata.max_degree || '-';
    }

    /**
     * Show node details in side panel.
     */
    showNodeDetails(nodeData, fullNodeData = null) {
        this.detailsPanel.classList.add('visible');
        
        // Title
        this.detailsTitle.textContent = nodeData.node_type === 'atomic' ? 'Atomic Node' : 'Context Node';
        
        // Build details HTML
        let html = '';
        
        // Node ID
        html += this.createDetailRow('Node ID', this.truncate(nodeData.nodeId, 30));
        
        // Type
        html += this.createDetailRow('Type', nodeData.node_type);
        
        // Degree
        html += this.createDetailRow('Degree', nodeData.degree);
        
        // Statement or context
        if (nodeData.node_type === 'atomic') {
            html += this.createDetailRow('Statement', nodeData.full_statement || nodeData.label);
            
            if (fullNodeData && fullNodeData.canonical_terms) {
                html += this.createDetailRow('Terms', fullNodeData.canonical_terms.join(', '));
            }
            
            if (fullNodeData && fullNodeData.evidence) {
                html += this.createDetailRow('Evidence', `${fullNodeData.evidence.length} source(s)`);
            }
        } else {
            if (fullNodeData && fullNodeData.source_file) {
                html += this.createDetailRow('Source File', fullNodeData.source_file);
            }
        }
        
        // Position
        const pos = `(${nodeData.x.toFixed(2)}, ${nodeData.y.toFixed(2)}, ${nodeData.z.toFixed(2)})`;
        html += this.createDetailRow('3D Position', pos);
        
        this.detailsContent.innerHTML = html;
    }

    /**
     * Close details panel.
     */
    closeDetails() {
        this.detailsPanel.classList.remove('visible');
    }

    /**
     * Create a detail row HTML.
     */
    createDetailRow(label, value) {
        return `
            <div class="detail-row">
                <div class="detail-label">${label}:</div>
                <div class="detail-value">${value || 'N/A'}</div>
            </div>
        `;
    }

    /**
     * Show loading overlay.
     */
    showLoading() {
        this.loadingPanel.classList.remove('hidden');
    }

    /**
     * Hide loading overlay.
     */
    hideLoading() {
        this.loadingPanel.classList.add('hidden');
    }

    /**
     * Truncate long strings.
     */
    truncate(str, maxLength) {
        if (!str) return '';
        if (str.length <= maxLength) return str;
        return str.substring(0, maxLength) + '...';
    }

    /**
     * Show error message.
     */
    showError(message) {
        alert(`Error: ${message}`);
    }

    /**
     * Setup view control event listeners.
     */
    setupViewControls(callbacks) {
        // LOD slider
        if (this.lodSlider) {
            this.lodSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                this.lodValue.textContent = value;
                if (callbacks.onLODChange) {
                    callbacks.onLODChange(value);
                }
            });
        }

        // Node scale slider
        if (this.nodeScaleSlider) {
            this.nodeScaleSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                this.nodeScaleValue.textContent = `${value}%`;
                if (callbacks.onNodeScaleChange) {
                    callbacks.onNodeScaleChange(value / 100);
                }
            });
        }
    }

    /**
     * Disable/enable refresh button.
     */
    setRefreshEnabled(enabled) {
        if (this.refreshBtn) {
            this.refreshBtn.disabled = !enabled;
        }
    }
}
