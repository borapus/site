// Optional audit tool; Lighthouse stays outside the website's runtime dependencies.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const options = Object.fromEntries(process.argv.slice(2).map(arg => {
  const split = arg.indexOf('=');
  if (!arg.startsWith('--') || split < 0) throw new Error('Use --name=value arguments.');
  return [arg.slice(2, split), arg.slice(split + 1)];
}));
const base = options.base || 'http://127.0.0.1:4322';
const host = new URL(base).hostname;
if (!['localhost', '127.0.0.1', '[::1]'].includes(host)) throw new Error('Audit the local build; remote audits require a separate explicit run.');
const cli = resolve(options.cli || '../seo-tools/node_modules/lighthouse/cli/index.js');
if (!existsSync(cli)) throw new Error('Install optional audit tool: npm install --prefix ../seo-tools --no-save lighthouse@13.5.0');
const output = resolve(options.output || '.seo/lighthouse');
mkdirSync(output, {recursive: true});
const paths = options.paths ? options.paths.split(',') : ['/en/', '/tr/', '/en/projects/', '/en/projects/hisaronu-house/', '/tr/projects/hisaronu-house/', '/en/studio/', '/en/contact/'];
for (const path of paths) {
  const url = new URL(path, base);
  if (url.origin !== new URL(base).origin) throw new Error('Audit path must stay on the local origin.');
  const filename = path.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'root';
  console.log(`Mobile Lighthouse: ${path}`);
  const child = spawn(process.execPath, [cli, url.href, '--chrome-flags=--headless', '--only-categories=performance,accessibility,best-practices,seo', '--output=json', `--output-path=${resolve(output, filename+'.json')}`, '--quiet'], {
    stdio: 'inherit', windowsHide: true,
    env: {...process.env, ...(options.chrome ? {CHROME_PATH: options.chrome} : {})},
  });
  await new Promise((done, fail) => {
    child.on('error', fail);
    child.on('exit', code => code === 0 ? done() : fail(new Error(`Lighthouse failed for ${path}: ${code}`)));
  });
}
console.log(`Reports saved in ${output}. Import with: python scripts/crawl-seo.py --performance-dir "${output}"`);
