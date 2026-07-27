const { exec } = require('child_process');

console.log("Starting build...");
exec('npm run build', { cwd: './frontend' }, (error, stdout, stderr) => {
  if (error) {
    console.error(`Error: ${error.message}`);
    return;
  }
  if (stderr) {
    console.error(`Stderr: ${stderr}`);
  }
  console.log(`Stdout: ${stdout}`);
});
