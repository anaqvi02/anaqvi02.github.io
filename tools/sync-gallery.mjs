import { readFile, writeFile } from 'node:fs/promises';
const root = new URL('../projects/', import.meta.url);
const files = JSON.parse(await readFile(new URL('items/index.json', root), 'utf8'));
if (!Array.isArray(files) || !files.length || new Set(files).size !== files.length || !files.every(file => /^[a-z0-9-]+\.html$/.test(file))) throw new Error('Invalid gallery manifest');
const cards = await Promise.all(files.map(file => readFile(new URL('items/' + file, root), 'utf8')));
for (const [index, card] of cards.entries()) {
 const id = files[index].slice(0, -5);
 if (!card.includes('data-project="' + id + '"') || (card.match(/<article\b/g) || []).length !== 1 || (card.match(/<\/article>/g) || []).length !== 1) throw new Error('Invalid project card: ' + files[index]);
}
const page = new URL('index.html', root);
const html = await readFile(page, 'utf8');
if (!html.includes('<!-- gallery:start -->') || !html.includes('<!-- gallery:end -->')) throw new Error('Gallery markers missing');
await writeFile(page, html.replace(/<!-- gallery:start -->[\s\S]*?<!-- gallery:end -->/, '<!-- gallery:start -->\n' + cards.join('\n') + '<!-- gallery:end -->'));
console.log('Synced ' + cards.length + ' project cards.');
