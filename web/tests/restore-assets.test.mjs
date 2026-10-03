import assert from 'node:assert/strict';
import {test} from 'node:test';
import {createHash} from 'node:crypto';
import {mkdtemp, mkdir, writeFile, readFile, copyFile, rm, readdir, symlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

const script = fileURLToPath(new URL('../scripts/restore-assets.mjs', import.meta.url));
const target = 'web/public/assets/avatar.glb', other = 'exports/avatar-uncompressed.glb';
const payload = Buffer.from('exact GLB bytes\0\u00ff'.repeat(100));
const record = (path, bytes) => ({path, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex')});

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'avatar-restore-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  async function write(name, data) {
    await mkdir(dirname(join(root, name)), {recursive: true});
    await writeFile(join(root, name), data);
  }
  await mkdir(join(root, 'web/scripts'), {recursive: true});
  await copyFile(script, join(root, 'web/scripts/restore-assets.mjs'));
  const parts = [];
  for (const [index, bytes] of [payload.subarray(0, 713), payload.subarray(713)].entries()) {
    const name = `delivery/parts/test/part-${String(index + 1).padStart(3, '0')}.bin`;
    await write(name, bytes);
    parts.push(record(name, bytes));
  }
  const manifest = {schemaVersion: 1, assets: [
    {...record(target, payload), parts}, {...record(other, payload), parts},
  ]};
  const save = () => write('config/delivery-parts.json', JSON.stringify(manifest));
  await save();
  async function run({args = [], success = true} = {}) {
    const result = spawnSync(process.execPath, [join(root, 'web/scripts/restore-assets.mjs'), ...args], {cwd: tmpdir(), encoding: 'utf8'});
    assert.equal(result.error, undefined);
    if (success) assert.equal(result.status, 0, result.stderr);
    else assert.notEqual(result.status, 0, result.stdout);
    assert.deepEqual((await readdir(root, {recursive: true})).filter(name => name.includes('.asset-restore-')), [], 'temporary files are cleaned up');
    return result;
  }
  return {root, write, parts, manifest, save, run};
}

test('restoration writes only the exact browser GLB and repeats safely', async t => {
  const f = await fixture(t);
  await f.run();
  assert.deepEqual(await readFile(join(f.root, target)), payload);
  await assert.rejects(readFile(join(f.root, other)), {code: 'ENOENT'});
  assert.match((await f.run()).stdout, /Already restored and verified/);
});

test('whole-asset alias streams its parts without creating its source target', async t => {
  const f = await fixture(t);
  f.manifest.assets[0].parts = [record(other, payload)];
  await f.save();
  await f.run();
  assert.deepEqual(await readFile(join(f.root, target)), payload);
  await assert.rejects(readFile(join(f.root, other)), {code: 'ENOENT'});
});

test('verify-only checks the package without creating directories or files', async t => {
  const f = await fixture(t), before = (await readdir(f.root, {recursive: true})).sort();
  assert.match((await f.run({args: ['--verify-only']})).stdout, /Verified/);
  assert.deepEqual((await readdir(f.root, {recursive: true})).sort(), before);
});

test('corrupt part blocks publication and is detected with an already-restored GLB', async t => {
  const f = await fixture(t);
  await f.write(f.parts[0].path, Buffer.alloc(f.parts[0].bytes, 120));
  assert.match((await f.run({success: false})).stderr, /SHA-256 mismatch/);
  await assert.rejects(readFile(join(f.root, target)), {code: 'ENOENT'});
  await f.write(target, payload);
  await f.run({success: false});
  assert.deepEqual(await readFile(join(f.root, target)), payload);
});

test('combined hash is checked independently of the individual parts', async t => {
  const f = await fixture(t);
  f.manifest.assets[0].sha256 = '0'.repeat(64);
  await f.save();
  assert.match((await f.run({success: false})).stderr, /SHA-256 mismatch/);
  await assert.rejects(readFile(join(f.root, target)), {code: 'ENOENT'});
});

test('existing local edits survive restoration and verify-only attempts', async t => {
  const f = await fixture(t);
  await f.write(target, 'user edited GLB');
  assert.match((await f.run({success: false})).stderr, /Refusing to overwrite/);
  await f.run({args: ['--verify-only'], success: false});
  assert.equal(await readFile(join(f.root, target), 'utf8'), 'user edited GLB');
});

test('missing part leaves no incomplete output', async t => {
  const f = await fixture(t);
  await rm(join(f.root, f.parts[1].path));
  await f.run({success: false});
  await assert.rejects(readFile(join(f.root, target)), {code: 'ENOENT'});
});

test('missing manifest safely preserves an older standalone GLB', async t => {
  const f = await fixture(t);
  await rm(join(f.root, 'config/delivery-parts.json'));
  await f.write(target, 'standalone GLB');
  assert.match((await f.run()).stdout, /No delivery-parts manifest/);
  assert.equal(await readFile(join(f.root, target), 'utf8'), 'standalone GLB');
});

test('unsafe relative paths and symlinked part paths are rejected', async t => {
  const f = await fixture(t), partName = f.parts[0].path;
  for (const name of ['../escape', '/tmp/escape', 'C:/escape', 'a\\escape', 'a/../escape']) {
    f.parts[0].path = name;
    await f.save();
    assert.match((await f.run({success: false})).stderr, /Unsafe repository-relative/);
  }
  f.parts[0].path = partName;
  await f.save();
  await f.write('original.bin', payload.subarray(0, 713));
  await rm(join(f.root, partName));
  await symlink(join(f.root, 'original.bin'), join(f.root, partName));
  assert.match((await f.run({success: false})).stderr, /Symlinks/);
});

test('symlinked output parent is rejected without writing through it', async t => {
  const f = await fixture(t);
  await mkdir(join(f.root, 'elsewhere'));
  await symlink(join(f.root, 'elsewhere'), join(f.root, 'web/public'), 'dir');
  assert.match((await f.run({success: false})).stderr, /Symlinks/);
  assert.deepEqual(await readdir(join(f.root, 'elsewhere')), []);
});

test('conflicting records, cyclic aliases, and a missing browser entry fail early', async t => {
  const f = await fixture(t);
  f.manifest.assets[0].parts = [{...record(other, payload), sha256: '0'.repeat(64)}];
  await f.save();
  assert.match((await f.run({success: false})).stderr, /Conflicting metadata/);
  f.manifest.assets[0].parts = [record(other, payload)];
  f.manifest.assets[1].parts = [record(target, payload)];
  await f.save();
  assert.match((await f.run({success: false})).stderr, /Cyclic asset parts/);
  f.manifest.assets = [{...record(other, payload), parts: f.parts}];
  await f.save();
  assert.match((await f.run({success: false})).stderr, /not in the delivery manifest/);
  await assert.rejects(readFile(join(f.root, target)), {code: 'ENOENT'});
});
