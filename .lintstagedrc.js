module.exports = {
  // JavaScript/React files
  '*.{js,jsx}': [
    'eslint --fix',
    'prettier --write',
  ],
  
  // Python files
  '*.py': [
    'python3 -m black --check',
    'python3 -m isort --check-only',
    'python3 -m flake8',
  ],
  
  // JSON and other files
  '*.{json,css,md}': [
    'prettier --write',
  ],
};