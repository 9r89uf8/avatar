// Byte-identical GLB restoration; Node built-ins only, including during npm hooks.
import {constants} from 'node:fs';
import {open, readFile, lstat, realpath, mkdir, link, unlink} from 'node:fs/promises';
import {createHash, randomUUID} from 'node:crypto';
import {dirname, resolve, relative, isAbsolute, sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const manifestName = 'config/delivery-parts.json';
const targetName = 'web/public/assets/avatar.glb';

async function containedPath(name) {
  if (typeof name !== 'string' || !name || /[\\:\0]/.test(name)
      || name.split('/').some(part => !part || part === '.' || part === '..')) {
    throw new Error(`Unsafe repository-relative path: ${JSON.stringify(name)}`);
  }
  let path = root;
  for (const component of name.split('/')) {
    path = resolve(path, component);
    let info;
    try { info = await lstat(path); } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    if (info?.isSymbolicLink()) throw new Error(`Symlinks are not allowed in delivery paths: ${name}`);
    if (info) {
      const within = relative(root, await realpath(path));
      if (isAbsolute(within) || within === '..' || within.startsWith(`..${sep}`)) {
        throw new Error(`Path escapes repository: ${name}`);
      }
    }
  }
  return path;
}

async function loadManifest() {
  const manifestPath = await containedPath(manifestName);
  let source;
  try { source = await readFile(manifestPath, 'utf8'); } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
  const data = JSON.parse(source);
  if (!data || data.schemaVersion !== 1 || !Array.isArray(data.assets)) {
    throw new Error('Unsupported delivery-parts manifest; expected schemaVersion 1');
  }
  const assets = new Map(), records = new Map();
  async function validate(record) {
    if (!record || typeof record !== 'object' || Array.isArray(record)) throw new Error('Each asset and part must be an object');
    await containedPath(record.path);
    if (!Number.isSafeInteger(record.bytes) || record.bytes < 0
        || typeof record.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(record.sha256)) {
      throw new Error(`Invalid byte count or SHA-256 for ${record.path}`);
    }
    const signature = `${record.bytes}:${record.sha256}`;
    if (records.has(record.path) && records.get(record.path) !== signature) throw new Error(`Conflicting metadata for ${record.path}`);
    records.set(record.path, signature);
  }
  for (const asset of data.assets) {
    await validate(asset);
    if (asset.path === manifestName || assets.has(asset.path)) throw new Error(`Duplicate or reserved asset path: ${asset.path}`);
    if (!Array.isArray(asset.parts) || !asset.parts.length) throw new Error(`Missing parts for ${asset.path}`);
    for (const part of asset.parts) await validate(part);
    if (asset.parts.reduce((sum, part) => sum + part.bytes, 0) !== asset.bytes) throw new Error(`Part byte counts do not sum to ${asset.path}`);
    assets.set(asset.path, asset);
  }
  const checked = new Set();
  function visit(name, active) {
    if (active.has(name)) throw new Error(`Cyclic asset parts at ${name}`);
    if (checked.has(name)) return;
    const next = new Set([...active, name]);
    for (const part of assets.get(name).parts) if (assets.has(part.path)) visit(part.path, next);
    checked.add(name);
  }
  for (const name of assets.keys()) visit(name, new Set());
  return assets;
}

async function* fileBlocks(record) {
  const path = await containedPath(record.path);
  const beforeOpen = await lstat(path);
  if (!beforeOpen.isFile() || beforeOpen.size !== record.bytes) throw new Error(`Missing, incomplete or corrupted file: ${record.path}`);
  const file = await open(path, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0));
  try {
    const info = await file.stat();
    if (!info.isFile() || info.size !== record.bytes) throw new Error(`Missing, incomplete or corrupted file: ${record.path}`);
    // A fresh buffer for each block remains valid while the consumer writes it.
    while (true) {
      const buffer = Buffer.allocUnsafe(1024 * 1024);
      const {bytesRead} = await file.read(buffer, 0, buffer.length, null);
      if (!bytesRead) break;
      yield buffer.subarray(0, bytesRead);
    }
  } finally { await file.close(); }
}

async function* verifiedBlocks(record, assets) {
  const hash = createHash('sha256');
  let bytes = 0;
  async function* source() {
    if (assets.has(record.path)) {
      for (const part of assets.get(record.path).parts) yield* verifiedBlocks(part, assets);
    } else yield* fileBlocks(record);
  }
  for await (const block of source()) {
    hash.update(block);
    bytes += block.length;
    yield block;
  }
  if (bytes !== record.bytes || hash.digest('hex') !== record.sha256) throw new Error(`Byte count or SHA-256 mismatch: ${record.path}`);
}

async function existingMatches(record) {
  const path = await containedPath(record.path);
  try { await lstat(path); } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
  try {
    const hash = createHash('sha256');
    for await (const block of fileBlocks(record)) hash.update(block);
    if (hash.digest('hex') === record.sha256) return true;
  } catch { /* Any unreadable/different target must remain untouched. */ }
  throw new Error(`Refusing to overwrite a different existing file: ${record.path}`);
}

async function restoreAsset(asset, assets, verifyOnly) {
  const target = await containedPath(asset.path);
  let alreadyExists = await existingMatches(asset), temporary, output;
  try {
    if (!verifyOnly && !alreadyExists) {
      await mkdir(dirname(target), {recursive: true});
      await containedPath(asset.path);
      const candidate = resolve(dirname(target), `.asset-restore-${randomUUID()}`);
      output = await open(candidate, 'wx', 0o600);
      temporary = candidate;
    }
    for await (const block of verifiedBlocks(asset, assets)) {
      if (output) {
        let offset = 0;
        while (offset < block.length) {
          const {bytesWritten} = await output.write(block, offset, block.length - offset, null);
          if (!bytesWritten) throw new Error('Unable to make progress writing restored asset');
          offset += bytesWritten;
        }
      }
    }
    if (output) {
      await output.sync();
      await output.close();
      output = null;
      await containedPath(asset.path);
      try {
        // Atomic, same-directory publication with no overwrite, including races.
        await link(temporary, target);
      } catch (error) {
        if (error.code !== 'EEXIST') throw error;
        await existingMatches(asset);
        alreadyExists = true;
      }
    }
    const status = verifyOnly ? 'Verified' : alreadyExists ? 'Already restored and verified' : 'Restored and verified';
    console.log(`${status}: ${asset.path} (${asset.bytes} bytes; SHA-256 ${asset.sha256})`);
  } finally {
    if (output) await output.close();
    if (temporary) await unlink(temporary);
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.some(arg => arg !== '--verify-only')) throw new Error('Usage: node scripts/restore-assets.mjs [--verify-only]');
  const assets = await loadManifest();
  if (assets === null) {
    console.log('No delivery-parts manifest; standalone assets need no restoration.');
    return;
  }
  if (!assets.has(targetName)) throw new Error(`Asset is not in the delivery manifest: ${targetName}`);
  await restoreAsset(assets.get(targetName), assets, args.includes('--verify-only'));
}

main().catch(error => {
  console.error(`Asset restoration failed: ${error.message}`);
  process.exitCode = 1;
});
