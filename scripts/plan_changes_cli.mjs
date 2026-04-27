import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const pythonScript = join(scriptDir, "plan_changes.py");
const python = process.env.PYTHON ?? "python";

const result = spawnSync(python, [pythonScript, ...process.argv.slice(2)], {
  stdio: "inherit",
  windowsHide: true,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
