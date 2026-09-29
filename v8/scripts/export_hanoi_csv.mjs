import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
const deps = path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const runtimeRequire = createRequire(path.join(deps, '_hanoi_loader.cjs'));
const { Workbook } = await import(pathToFileURL(runtimeRequire.resolve('@oai/artifact-tool')).href);

const dir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../data/hanoi_teaching');
const source = path.join(dir, '2026-09-29.jsonl');
const output = path.join(dir, 'hanoi_poses_2026-09-29.csv');
const lines = (await fs.readFile(source, 'utf8')).trim().split(/\r?\n/);
const records = lines.map((line, i) => ({...JSON.parse(line), sourceLine:i+1}))
  .filter(r => r.event === 'pose_capture');
const names = ['shoulder_pan','shoulder_lift','elbow','wrist_1','wrist_2','wrist_3'];
const headers = ['capture_id','captured_utc','peg','location','pose_role','teaching_method','tcp_frame',
  'tcp_x_m','tcp_y_m','tcp_z_m','tcp_qx','tcp_qy','tcp_qz','tcp_qw',
  ...names.map(n=>`${n}_rad`), ...names.map(n=>`${n}_velocity_rad_s`),
  'tool_output_0','tool_output_1','processing','replay_validated','source_file','source_line',
  'note_post_clearance','note_freedrive'];
const rows = records.map(r => {
  const match = /^peg(\d+)_location(\d+)_(.+)$/.exec(r.name);
  if (!match) throw new Error(`Unmapped pose name: ${r.name}`);
  const q = names.map(n=>r.joint_positions_rad[r.joint_names.indexOf(`${n}_joint`)]);
  const v = names.map(n=>r.joint_velocities_rad_s[r.joint_names.indexOf(`${n}_joint`)]);
  if (![...q,...v,...r.tcp_position_m,...r.tcp_quaternion_xyzw].every(Number.isFinite)) throw new Error('Invalid measurement');
  return [r.name, r.utc, Number(match[1]), Number(match[2]), match[3], 'freedrive', r.tcp_frame,
    ...r.tcp_position_m, ...r.tcp_quaternion_xyzw, ...q, ...v,
    r.tool_outputs['16'],r.tool_outputs['17'],'raw_unadjusted',false,
    '2026-09-29.jsonl',r.sourceLine,
    'Luke: each stack is on a post. Lift straight up the post before lateral transfer. Post ends just above location 6; location 7 is not feasible. Clearance height remains to be measured.',
    'Luke: all poses are taught in freedrive and may need consistency adjustments. Preserve raw data; record any later adjusted targets separately.'];
});
if (!rows.length) throw new Error('No pose captures');
const wb = Workbook.create();
const sheet = wb.worksheets.add('Pose captures');
const matrix = [headers,...rows];
const range = sheet.getRangeByIndexes(0,0,matrix.length,headers.length);
range.values = matrix;
wb.recalculate();
const values = range.values;
for (let r=0;r<matrix.length;r++) for(let c=0;c<headers.length;c++) {
  if(typeof matrix[r][c] !== 'string' && values[r][c] !== matrix[r][c]) throw new Error(`Cell mismatch ${r},${c}`);
}
await wb.inspect({kind:'table',range:'\'Pose captures\'!A1:G2',include:'values',tableMaxRows:2,tableMaxCols:7,maxChars:1600});
// CSV has no style or formulas. Export the verified scalar values at full JS numeric precision.
const field = value => {
  const text=String(value ?? '');
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"','""')}"` : text;
};
// Preserve original text, especially ISO timestamps that a workbook may interpret as dates.
const exportValues = values.map((row,r)=>row.map((v,c)=>typeof matrix[r][c] === 'string' ? matrix[r][c] : v));
const temporary = `${output}.${process.pid}.tmp`;
await fs.writeFile(temporary,exportValues.map(row=>row.map(field).join(',')).join('\r\n')+'\r\n','utf8');
// Re-import the saved CSV using the public reader and check the measurement columns.
const imported = await Workbook.fromCSV(await fs.readFile(temporary,'utf8'),{sheetName:'Saved CSV'});
const saved = imported.worksheets.getItemAt(0).getRangeByIndexes(0,0,matrix.length,headers.length).values;
for(let r=1;r<matrix.length;r++) for(let c=7;c<26;c++) {
  if(Number(saved[r][c]) !== matrix[r][c]) throw new Error(`CSV numeric mismatch ${r},${c}`);
}
await fs.rename(temporary, output);
console.log(JSON.stringify({output,rows:rows.length,columns:headers.length,numericRoundTrip:'passed'}));
