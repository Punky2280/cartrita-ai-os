#!/usr/bin/env node
/* eslint-env node */
/* eslint-disable no-console */

const fs = require('fs');
const path = require('path');

// Function to recursively find TypeScript/JavaScript files
function findFiles(dir, extensions = ['.ts', '.tsx', '.js', '.jsx']) {
  const files = [];
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      files.push(...findFiles(fullPath, extensions));
    } else if (stat.isFile() && extensions.some(ext => item.endsWith(ext))) {
      files.push(fullPath);
    }
  }

  return files;
}

// Function to apply fixes to a file
function fixFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let changed = false;

  // Replace 'any' types with 'unknown' (safer approach)
  const anyReplacements = [
    // Function parameters and return types
    { from: /: any\b/g, to: ': unknown' },
    { from: /<any>/g, to: '<unknown>' },
    { from: /<any\[\]>/g, to: '<unknown[]>' },
    { from: /Record<string, any>/g, to: 'Record<string, unknown>' },
    { from: /\[\] = \[\] as any/g, to: '[] = [] as unknown[]' },

    // Arrow functions with improper spacing
    { from: /onClick=\{[^}]*\(\) => ([^}]+)\}/g, to: (match, action) => {
      return `onClick={() => { ${action.trim()}; }}`;
    }},
    { from: /onChange=\{[^}]*\([^)]*\) => ([^}]+)\}/g, to: (match) => {
      return match.replace(/=> ([^}]+)/, '=> { $1; }');
    }},

    // Fix void promises
    { from: /navigator\.clipboard\.writeText\(/g, to: 'void navigator.clipboard.writeText(' },
    { from: /queryClient\.invalidateQueries\(/g, to: 'void queryClient.invalidateQueries(' },
    { from: /audioContextRef\.current\.close\(/g, to: 'void audioContextRef.current.close(' },
  ];

  anyReplacements.forEach(({ from, to }) => {
    const original = content;
    if (typeof to === 'function') {
      content = content.replace(from, to);
    } else {
      content = content.replace(from, to);
    }
    if (content !== original) {
      changed = true;
    }
  });

  // Note: Advanced unused variable removal would require AST parsing
  // This is left as a placeholder for future enhancements

  if (changed) {
    fs.writeFileSync(filePath, content);
    console.log(`Fixed: ${filePath}`);
  }

  return changed;
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const files = findFiles(srcDir);

console.log(`Found ${files.length} files to process...`);

let totalFixed = 0;
files.forEach(file => {
  if (fixFile(file)) {
    totalFixed++;
  }
});

console.log(`\nFixed ${totalFixed} files.`);
console.log('Run "npm run lint" to see remaining issues.');
