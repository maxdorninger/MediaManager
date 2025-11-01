import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { enhancedImages } from '@sveltejs/enhanced-img';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [tailwindcss(), enhancedImages(), sveltekit()],
	server: {
		host: '0.0.0.0', // Allow external connections (required for Docker)
		port: 5173,
		strictPort: true, // Fail if port is already in use
		watch: {
			usePolling: true, // Required for file watching in Docker on some systems
			interval: 100 // Check for changes every 100ms
		},
		proxy: {
			// Proxy API requests to backend container
			'/api': {
				target: 'http://mediamanager:8000',
				changeOrigin: true
			}
		}
	}
});
