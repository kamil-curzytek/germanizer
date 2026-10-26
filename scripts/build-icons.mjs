// Writes the app icons in public/ (home-screen install + push notifications): a bold white "L" on the
// brand green, like the favicon in index.html. No dependencies: a minimal PNG encoder on node:zlib.
//   node scripts/build-icons.mjs
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { crc32, deflateSync } from 'node:zlib';

const out = join(import.meta.dirname, '..', 'public');
const GREEN = [0x2f, 0x5d, 0x50, 255];
const WHITE = [255, 255, 255, 255];
const CLEAR = [0, 0, 0, 0];

// "L" as two rectangles in unit coordinates: [x0, y0, x1, y1]
const L = [
  [0.36, 0.24, 0.49, 0.76], // stem
  [0.36, 0.63, 0.66, 0.76], // foot
];

function png(size, { background, foreground, scale = 1 }) {
  const rows = [];
  for (let y = 0; y < size; y++) {
    const row = Buffer.alloc(1 + size * 4); // filter byte 0 + RGBA
    for (let x = 0; x < size; x++) {
      // 4x4 supersampling for clean edges
      let hits = 0;
      for (let sy = 0; sy < 4; sy++)
        for (let sx = 0; sx < 4; sx++) {
          const u = 0.5 + ((x + (sx + 0.5) / 4) / size - 0.5) / scale;
          const v = 0.5 + ((y + (sy + 0.5) / 4) / size - 0.5) / scale;
          if (L.some(([x0, y0, x1, y1]) => u >= x0 && u < x1 && v >= y0 && v < y1)) hits++;
        }
      const a = hits / 16;
      const px = background.map((b, i) => Math.round(b * (1 - a) + foreground[i] * a));
      row.set(px, 1 + x * 4);
    }
    rows.push(row);
  }
  const chunk = (type, data) => {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(body));
    return Buffer.concat([len, body, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // RGBA
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(Buffer.concat(rows), { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

const icons = {
  'icon-192.png': png(192, { background: GREEN, foreground: WHITE }),
  'icon-512.png': png(512, { background: GREEN, foreground: WHITE }),
  'apple-touch-icon.png': png(180, { background: GREEN, foreground: WHITE }),
  // Android status-bar badge: only the alpha channel is used
  'badge-96.png': png(96, { background: CLEAR, foreground: WHITE, scale: 1.4 }),
};
for (const [name, data] of Object.entries(icons)) {
  writeFileSync(join(out, name), data);
  console.log(`public/${name}  ${data.length} bytes`);
}
