// Bulletproof Windows Wrapper for n8n Process Execution
// Senior DevOps Automation Standard

const { spawn } = require('child_process');
const path = require('path');

const n8nBin = path.join(__dirname, 'node_modules', 'n8n', 'bin', 'n8n');

console.log(`[Wrapper] Spawning native n8n execution via child_process...`);
console.log(`[Wrapper] Binary Path: ${n8nBin}`);

const n8nProcess = spawn('node', [n8nBin, 'start'], {
  cwd: __dirname,
  env: process.env,
  shell: true, // Enables stable execution environment on Windows shell context
  stdio: 'pipe' // Capture output streams explicitly
});

// Explicitly handle output logging to support PM2's capture mechanism
n8nProcess.stdout.on('data', (data) => {
  process.stdout.write(data);
});

n8nProcess.stderr.on('data', (data) => {
  process.stderr.write(data);
});

n8nProcess.on('close', (code) => {
  console.log(`[Wrapper] Native n8n process exited with status code: ${code}`);
  process.exit(code);
});

// Forward termination signals to n8n process
process.on('SIGINT', () => n8nProcess.kill('SIGINT'));
process.on('SIGTERM', () => n8nProcess.kill('SIGTERM'));
