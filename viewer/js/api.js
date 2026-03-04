/**
 * API client for fetching snapshot data from Flask backend.
 */

export class API {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * Fetch 3D snapshot data from server.
     */
    async fetchSnapshot() {
        try {
            const response = await fetch(`${this.baseUrl}/api/snapshot`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch snapshot:', error);
            throw error;
        }
    }

    /**
     * Fetch detailed node information.
     */
    async fetchNodeDetails(nodeId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/node/${nodeId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch node details:', error);
            throw error;
        }
    }

    /**
     * Check server health.
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error' };
        }
    }
}
