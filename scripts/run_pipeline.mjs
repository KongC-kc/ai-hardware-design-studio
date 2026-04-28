import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const script = join(__dirname, "run_pipeline.py");

const result = spawnSync("python", [script, ...process.argv.slice(2)], {
  stdio: "inherit",
});

process.exitCode = result.status ?? 1;
