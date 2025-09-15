/*
PURPOSE: Vite bundler configuration for React development

KEY COMPONENTS:
- React plugin for JSX support
- Build optimization settings
- Development server configuration

WHY USED:
- Fast development server with hot module replacement
- Optimized production builds
- Modern JavaScript bundling
*/

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
});
