const fs = require('fs');
const path = require('path');
const http = require('http');

console.log('====================================================');
console.log('     n8n LOCAL SELF-HOSTED ENVIRONMENT VERIFICATION  ');
console.log('====================================================');

let success = true;

// 1. Check .env exists & correct variables
const envPath = path.join(__dirname, '.env');
console.log(`[1] Verifying .env configuration...`);
if (!fs.existsSync(envPath)) {
  console.error('[-] ERROR: .env file is missing!');
  success = false;
} else {
  const envContent = fs.readFileSync(envPath, 'utf8');
  
  const checkVar = (varName, expectedSub) => {
    const match = envContent.match(new RegExp(`^${varName}=(.*)$`, 'm'));
    if (!match) {
      console.error(`[-] ERROR: Variable ${varName} is missing in .env!`);
      success = false;
    } else {
      const val = match[1].trim();
      if (expectedSub && !val.includes(expectedSub)) {
        console.error(`[-] ERROR: Variable ${varName} value is "${val}", expected it to contain "${expectedSub}"`);
        success = false;
      } else {
        console.log(`[+] SUCCESS: ${varName} is configured correctly (${val})`);
      }
    }
  };

  checkVar('NODES_EXCLUDE', '[]');
  checkVar('N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS', 'false');
  checkVar('N8N_PORT', '5679');
  checkVar('N8N_DATABASE_TYPE', 'sqlite');
}

// 2. Check dependencies
console.log(`\n[2] Verifying package dependencies...`);
const pkgPath = path.join(__dirname, 'package.json');
if (!fs.existsSync(pkgPath)) {
  console.error('[-] ERROR: package.json is missing!');
  success = false;
} else {
  try {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    if (pkg.dependencies && pkg.dependencies.n8n && pkg.dependencies.pm2) {
      console.log(`[+] SUCCESS: package.json contains 'n8n' and 'pm2' dependencies`);
    } else {
      console.error('[-] ERROR: package.json is missing n8n or pm2 in dependencies!');
      success = false;
    }
  } catch (err) {
    console.error('[-] ERROR: package.json is not valid JSON!', err.message);
    success = false;
  }
}

// 3. Check node_modules exists
console.log(`\n[3] Verifying local Node modules existence...`);
const nodeModulesPath = path.join(__dirname, 'node_modules');
if (!fs.existsSync(nodeModulesPath)) {
  console.warn('[-] WARNING: node_modules folder is missing. Installation is required.');
  success = false;
} else {
  console.log(`[+] SUCCESS: node_modules folder exists`);
}

// 4. Check active n8n instance health if started
console.log(`\n[4] Probing active local n8n instance health...`);
const req = http.get('http://localhost:5679/healthz', (res) => {
  if (res.statusCode === 200) {
    console.log(`[+] SUCCESS: Local n8n instance is running and fully healthy!`);
    finalize();
  } else {
    console.warn(`[-] WARNING: Probed local n8n returned HTTP status ${res.statusCode}. It may still be booting or offline.`);
    finalize();
  }
});

req.on('error', (e) => {
  console.log(`[-] n8n API probe: Instance is currently offline or loading (normal if not yet started).`);
  finalize();
});

req.end();

function finalize() {
  console.log('\n====================================================');
  if (success) {
    console.log(' STATUS: ALL CORE CONFIGURATIONS PASS SYSTEM AUDIT');
    console.log(' Ready to start/run! Run: .\\n8n-control.ps1 start');
  } else {
    console.error(' STATUS: VERIFICATION FAILED. Please resolve the errors highlighted above.');
  }
  console.log('====================================================');
}
