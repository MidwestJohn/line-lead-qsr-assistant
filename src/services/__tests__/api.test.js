// Mock the ConnectionManager module
jest.mock('../ConnectionManager', () => ({
  connectionManager: {
    makeRequest: jest.fn(),
    isConnected: jest.fn(() => true),
  },
}));

import { apiService } from '../api';

// Mock fetch globally
global.fetch = jest.fn();

describe('APIService', () => {
  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllMocks();
  });

  describe('get method', () => {
    it('should make a GET request successfully', async () => {
      const mockResponse = { status: 'success', data: 'test' };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.get('/test-endpoint');
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test-endpoint'),
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiService.get('/test-endpoint')).rejects.toThrow('Network error');
    });
  });

  describe('post method', () => {
    it('should make a POST request with data', async () => {
      const mockResponse = { status: 'success' };
      const testData = { message: 'test' };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.post('/chat', testData);
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(testData),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });
});