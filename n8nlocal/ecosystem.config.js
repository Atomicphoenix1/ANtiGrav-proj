const path = require('path');
const fs = require('fs');

// Synchronously read and parse the local .env file
const envConfig = {};
try {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const envLines = fs.readFileSync(envPath, 'utf8').split('\n');
    envLines.forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const index = trimmed.indexOf('=');
        if (index > -1) {
          const key = trimmed.substring(0, index).trim();
          let value = trimmed.substring(index + 1).trim();
          // Remove potential wrapping quotes
          if (value.startsWith('"') && value.endsWith('"')) {
            value = value.substring(1, value.length - 1);
          } else if (value.startsWith("'") && value.endsWith("'")) {
            value = value.substring(1, value.length - 1);
          }
          envConfig[key] = value;
        }
      }
    });
  }
} catch (err) {
  console.error('Failed to parse .env file:', err);
}

module.exports = {
  apps: [
    {
      name: 'n8n-local',
      script: path.join(__dirname, 'node_modules', 'n8n', 'bin', 'n8n'),
      args: 'start',
      interpreter: 'node',
      cwd: __dirname,
      watch: false,
      autorestart: true,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        ...envConfig
      },
      // Log to workspace logs directory
      error_file: path.join(__dirname, 'logs', 'error.log'),
      out_file: path.join(__dirname, 'logs', 'output.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    }
  ]
};