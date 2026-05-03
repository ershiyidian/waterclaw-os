#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import { copyFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const isWindows = process.platform === 'win32';
const npmCmd = 'npm';
const condaCmd = 'conda';
const viteEntry = join(repoRoot, 'node_modules', 'vite', 'bin', 'vite.js');
const vueTscEntry = join(repoRoot, 'node_modules', 'vue-tsc', 'bin', 'vue-tsc.js');

function commandSpec(command, args) {
  if (!isWindows || command.includes('\\') || command.includes('/')) return { command, args, shell: false };
  return { command: 'cmd.exe', args: ['/d', '/s', '/c', command, ...args], shell: false };
}

function usage() {
  console.log(`WaterClaw OS CLI

Usage:
  waterclaw <command> [options]

Commands:
  install              Install frontend deps and create/update the Conda backend env
  dev                  Start backend and frontend together
  frontend             Start only the Vite HMI
  backend              Start only the FastAPI Agent Host
  mcp                  Start the WaterClaw MCP stdio server
  build                Type-check and build the frontend
  test                 Run protocol simulation tests
  doctor               Check local toolchain and key files
  clean                Remove generated local artifacts
  help                 Show this help

Options:
  --env <name>         Conda env name, default: waterclaw-llm
  --no-npm-install     Skip npm install in install
  --no-backend-env     Skip Conda backend env install in install
`);
}

function parse(argv) {
  const args = [...argv];
  const command = args.shift() ?? 'help';
  const options = {
    envName: process.env.WATERCLAW_CONDA_ENV || 'waterclaw-llm',
    npmInstall: true,
    backendEnv: true,
  };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--env') {
      options.envName = args[index + 1];
      index += 1;
    } else if (arg === '--no-npm-install') {
      options.npmInstall = false;
    } else if (arg === '--no-backend-env') {
      options.backendEnv = false;
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }
  if (!/^[A-Za-z0-9_.-]+$/.test(options.envName)) {
    throw new Error('Invalid Conda env name. Use only letters, numbers, dot, underscore, or dash.');
  }
  return { command, options };
}

function spawnProcess(command, args, options = {}) {
  const spec = commandSpec(command, args);
  const child = spawn(spec.command, spec.args, {
    cwd: repoRoot,
    stdio: options.stdio ?? 'inherit',
    shell: spec.shell,
    env: {
      ...process.env,
      PYTHONNOUSERSITE: '1',
      LITELLM_LOCAL_MODEL_COST_MAP: 'True',
      WATERCLAW_CONDA_ENV: options.envName ?? process.env.WATERCLAW_CONDA_ENV ?? 'waterclaw-llm',
      ...(options.env ?? {}),
    },
  });
  if (options.label) child.on('exit', (code) => console.log(`[${options.label}] exited with code ${code ?? 0}`));
  return child;
}

function run(command, args, options = {}) {
  const spec = commandSpec(command, args);
  const result = spawnSync(spec.command, spec.args, {
    cwd: repoRoot,
    stdio: options.stdio ?? 'inherit',
    shell: spec.shell,
    env: {
      ...process.env,
      PYTHONNOUSERSITE: '1',
      LITELLM_LOCAL_MODEL_COST_MAP: 'True',
      WATERCLAW_CONDA_ENV: options.envName ?? process.env.WATERCLAW_CONDA_ENV ?? 'waterclaw-llm',
      ...(options.env ?? {}),
    },
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function check(command, args, options = {}) {
  const spec = commandSpec(command, args);
  const result = spawnSync(spec.command, spec.args, {
    cwd: repoRoot,
    stdio: 'pipe',
    shell: spec.shell,
    encoding: 'utf8',
    env: { ...process.env, ...(options.env ?? {}) },
  });
  return { ok: result.status === 0, output: `${result.stdout ?? ''}${result.stderr ?? ''}`.trim() };
}

function powershellCheck(commandText) {
  const result = spawnSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', commandText], {
    cwd: repoRoot,
    stdio: 'pipe',
    shell: false,
    encoding: 'utf8',
  });
  return { ok: result.status === 0, output: `${result.stdout ?? ''}${result.stderr ?? ''}`.trim() };
}

function install(options) {
  if (options.npmInstall) run(npmCmd, ['install'], options);
  if (options.backendEnv) runScript('backend/create-conda-env.ps1', options);
  ensureEnvFile();
}

function runScript(script, options) {
  if (isWindows) {
    run('powershell', ['-ExecutionPolicy', 'Bypass', '-File', script], options);
    return;
  }
  run('pwsh', ['-File', script], options);
}

function ensureEnvFile() {
  const envFile = join(repoRoot, 'backend', '.env');
  const example = join(repoRoot, 'backend', '.env.example');
  if (!existsSync(envFile) && existsSync(example)) {
    copyFileSync(example, envFile);
    console.log('Created backend/.env from backend/.env.example. Edit provider keys before using live LLM calls.');
  }
}

function backend(options) {
  run(condaCmd, [
    'run',
    '--no-capture-output',
    '-n',
    options.envName,
    'python',
    '-s',
    '-m',
    'uvicorn',
    'app.main:app',
    '--app-dir',
    'backend',
    '--host',
    '127.0.0.1',
    '--port',
    '8787',
    '--reload',
  ], options);
}

function frontend(options) {
  run(process.execPath, [viteEntry, '--host', '127.0.0.1'], options);
}

function mcp(options) {
  run(condaCmd, [
    'run',
    '--no-capture-output',
    '-n',
    options.envName,
    'python',
    '-s',
    '-m',
    'app.mcp.fastmcp_server',
    '--transport',
    'stdio',
  ], { ...options, env: { PYTHONPATH: join(repoRoot, 'backend') } });
}

function build(options) {
  run(process.execPath, [vueTscEntry, '--noEmit'], options);
  run(process.execPath, [viteEntry, 'build'], options);
}

function dev(options) {
  ensureEnvFile();
  const backendProc = spawnProcess(condaCmd, [
    'run',
    '--no-capture-output',
    '-n',
    options.envName,
    'python',
    '-s',
    '-m',
    'uvicorn',
    'app.main:app',
    '--app-dir',
    'backend',
    '--host',
    '127.0.0.1',
    '--port',
    '8787',
    '--reload',
  ], { ...options, label: 'backend' });
  const frontendProc = spawnProcess(process.execPath, [viteEntry, '--host', '127.0.0.1'], { ...options, label: 'frontend' });

  const stop = () => {
    for (const child of [backendProc, frontendProc]) {
      if (!child.killed) child.kill('SIGTERM');
    }
  };
  process.on('SIGINT', () => {
    stop();
    process.exit(130);
  });
  process.on('SIGTERM', () => {
    stop();
    process.exit(143);
  });
}

function doctor(options) {
  const checks = [
    ['Node', process.execPath, ['--version']],
    ['npm', npmCmd, ['--version']],
    ['Conda', condaCmd, ['--version']],
  ];
  let failed = false;
  for (const [label, command, args] of checks) {
    const result = check(command, args);
    console.log(`${result.ok ? 'ok ' : 'ERR'} ${label}: ${result.output || 'not found'}`);
    if (!result.ok) failed = true;
  }

  const required = ['package.json', 'backend/environment.yml', 'backend/requirements.txt', 'backend/app/main.py'];
  for (const file of required) {
    const ok = existsSync(join(repoRoot, file));
    console.log(`${ok ? 'ok ' : 'ERR'} ${file}`);
    if (!ok) failed = true;
  }

  const envFile = existsSync(join(repoRoot, 'backend', '.env'));
  console.log(`${envFile ? 'ok ' : 'warn'} backend/.env${envFile ? '' : ' missing; run waterclaw install or copy backend/.env.example'}`);

  const env = check(
    condaCmd,
    ['run', '-n', options.envName, 'python', '-s', '-m', 'app.doctor'],
    { env: { PYTHONPATH: join(repoRoot, 'backend'), PYTHONNOUSERSITE: '1' } },
  );
  console.log(`${env.ok ? 'ok ' : 'ERR'} Conda env ${options.envName}: ${env.output || 'not ready'}`);
  if (!env.ok) failed = true;

  if (failed) process.exit(1);
}

function clean() {
  const targets = ['dist', 'coverage', 'backend/.waterclaw', 'backend/backend'];
  const script = [
    "$ErrorActionPreference='Stop'",
    `$workspace=(Resolve-Path -LiteralPath '${repoRoot.replaceAll("'", "''")}').Path`,
    ...targets.map((target) => {
      const path = join(repoRoot, target).replaceAll("'", "''");
      return `if (Test-Path -LiteralPath '${path}') { $resolved=(Resolve-Path -LiteralPath '${path}').Path; if (-not $resolved.StartsWith($workspace,[System.StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to remove $resolved" }; Remove-Item -LiteralPath $resolved -Recurse -Force }`;
    }),
  ].join('; ');

  if (isWindows) run('powershell', ['-NoProfile', '-Command', script]);
  else run('pwsh', ['-NoProfile', '-Command', script]);
}

try {
  const { command, options } = parse(process.argv.slice(2));
  switch (command) {
    case 'install':
      install(options);
      break;
    case 'dev':
      dev(options);
      break;
    case 'frontend':
      frontend(options);
      break;
    case 'backend':
      backend(options);
      break;
    case 'mcp':
      mcp(options);
      break;
    case 'build':
      build(options);
      break;
    case 'test':
      run('python', ['-m', 'tests.simulation.run_illegal_discharge_simulation'], options);
      break;
    case 'doctor':
      doctor(options);
      break;
    case 'clean':
      clean();
      break;
    case 'help':
    case '--help':
    case '-h':
      usage();
      break;
    default:
      usage();
      process.exit(1);
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
