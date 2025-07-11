/**
 * 🌐 Enhanced API Service with Connection Management
 * 
 * Wraps all API calls with intelligent connection management, retry logic,
 * and session persistence for reliable restaurant environment operation.
 */

import { connectionManager } from './ConnectionManager';

class APIService {
    constructor() {
        this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    }

    // Core HTTP methods with connection management
    async get(endpoint, options = {}) {
        return this.makeRequest(endpoint, {
            method: 'GET',
            ...options
        });
    }

    async post(endpoint, data, options = {}) {
        return this.makeRequest(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: JSON.stringify(data),
            ...options
        });
    }

    async postFormData(endpoint, formData, options = {}) {
        return this.makeRequest(endpoint, {
            method: 'POST',
            body: formData,
            ...options
        });
    }

    async delete(endpoint, options = {}) {
        return this.makeRequest(endpoint, {
            method: 'DELETE',
            ...options
        });
    }

    // Connection-managed request wrapper
    async makeRequest(endpoint, options) {
        try {
            const response = await connectionManager.makeRequest(endpoint, options);
            
            // Handle response based on content type
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                return { success: true, data, response };
            } else {
                return { success: true, response };
            }
            
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            return { 
                success: false, 
                error: error.message,
                code: error.code || 'NETWORK_ERROR'
            };
        }
    }

    // Specific API endpoints with error handling
    async sendChatMessage(message) {
        const result = await this.post('/chat', { message });
        if (!result.success) {
            throw new Error(`Chat failed: ${result.error}`);
        }
        return result.data;
    }

    async sendMultiModalMessage(message, currentEquipment = null, enableCitations = true) {
        const result = await this.post('/voice-with-multimodal-citations', {
            message,
            current_equipment: currentEquipment,
            enable_citations: enableCitations
        });
        if (!result.success) {
            throw new Error(`Multimodal chat failed: ${result.error}`);
        }
        return result.data;
    }

    async uploadFile(file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const result = await this.postFormData('/upload', formData);
            if (!result.success) {
                throw new Error(`Upload failed: ${result.error}`);
            }
            return result.data;
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }

    async uploadFileWithProgress(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Use the simple, reliable upload endpoint
            const result = await this.postFormData('/upload-simple', formData);
            if (!result.success) {
                throw new Error(`Simple upload failed: ${result.error}`);
            }
            return result;
        } catch (error) {
            console.error('Simple file upload failed:', error);
            throw error;
        }
    }

    async getProcessingStatus(processId) {
        const result = await this.get(`/api/v2/processing-status/${processId}`);
        if (!result.success) {
            console.warn('Failed to get processing status:', result.error);
            return null;
        }
        return result.data;
    }

    async getProcessingResult(processId) {
        const result = await this.get(`/api/v2/processing-result/${processId}`);
        if (!result.success) {
            console.warn('Failed to get processing result:', result.error);
            return null;
        }
        return result.data;
    }

    async getDocuments() {
        const result = await this.get('/documents');
        if (!result.success) {
            console.warn('Failed to fetch documents:', result.error);
            return { documents: [], total_count: 0 };
        }
        return result.data;
    }

    async deleteDocument(documentId) {
        const result = await this.delete(`/documents/${documentId}`);
        if (!result.success) {
            throw new Error(`Delete failed: ${result.error}`);
        }
        return result.data;
    }

    async searchDocuments(query) {
        const result = await this.post('/search', { query });
        if (!result.success) {
            console.warn('Search failed:', result.error);
            return { results: [], message: 'Search temporarily unavailable' };
        }
        return result.data;
    }

    async getHealth() {
        const result = await this.get('/health');
        if (!result.success) {
            return { status: 'error', error: result.error };
        }
        return result.data;
    }

    async warmUpServer() {
        try {
            const result = await this.post('/warm-up', {});
            return result.success ? result.data : { status: 'failed', error: result.error };
        } catch (error) {
            return { status: 'failed', error: error.message };
        }
    }

    // Utility methods
    getConnectionStatus() {
        return connectionManager.getStatus();
    }

    forceReconnect() {
        return connectionManager.forceReconnect();
    }

    addConnectionListener(callback) {
        return connectionManager.addListener(callback);
    }

    // File URL generator
    getFileUrl(filename) {
        return `${this.baseURL}/files/${filename}`;
    }
}

// Singleton instance
export const apiService = new APIService();
export default APIService;