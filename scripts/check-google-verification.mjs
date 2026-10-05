import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';

// Owner-required permanent Search Console verification asset.
const filename = 'googled2ce318fd0d40c1d.html';
const directory = process.argv[2] || 'public';
assert.equal(
  readFileSync(join(directory, filename), 'utf8').trim(),
  `google-site-verification: ${filename}`,
  'Permanent Google verification file is missing or modified. Restore the original file before publishing.',
);
console.log(`Google verification file preserved in ${directory}.`);
