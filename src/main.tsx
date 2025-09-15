import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
/*
 React Application Entry Point
**Purpose**: Bootstraps the React application
**Key Components**:
```tsx
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```
**Why Used**:
- Standard React 18 application setup
- Strict mode for development warnings
- Root element mounting

### Frontend Configuration Files
- **`package.json`**: Dependencies and scripts for React app
- **`vite.config.ts`**: Vite bundler configuration
- **`tailwind.config.js`**: Tailwind CSS styling configuration
- **`tsconfig.json`**: TypeScript configuration
- **`eslint.config.js`**: Code linting rules

**Why Used**: Standard modern React development stack with TypeScript, Vite, and Tailwind CSS for fast development and professional styling.
*/