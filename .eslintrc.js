module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 12,
    sourceType: 'module',
  },
  plugins: [
    'react',
    'react-hooks',
    'jsx-a11y',
  ],
  rules: {
    // Error prevention
    'no-unused-vars': 'error',
    'no-console': 'warn',
    'no-debugger': 'error',
    
    // React specific
    'react/prop-types': 'warn',
    'react/react-in-jsx-scope': 'off', // Not needed in React 17+
    'react/jsx-uses-react': 'off',
    'react/jsx-uses-vars': 'error',
    
    // Accessibility
    'jsx-a11y/alt-text': 'error',
    'jsx-a11y/aria-role': 'error',
    
    // Code quality
    'prefer-const': 'error',
    'no-var': 'error',
    'eqeqeq': 'error',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};