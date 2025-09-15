#!/usr/bin/env node
/*
  Native Codacy MCP replacement focused on local CLI invocation without unintended 'wsl' prefix.
  Supported JSON-RPC 2.0 methods:
    - initialize
    - shutdown
    - analyze { file?: string, format?: string }
  Returns SARIF content inside result.sarif for analyze.
  Scope intentionally minimal: extend only if necessary for additional Codacy MCP features.
*/

import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import process from 'node:process'

const JSONRPC_VERSION = '2.0'
const CLI_RELATIVE = '.codacy/cli.sh'

function findCli(startDir) {
  let dir = startDir
  while (true) {
    const candidate = resolve(dir, CLI_RELATIVE)
    if (existsSync(candidate)) return candidate
    const parent = dirname(dir)
    if (parent === dir) break
    dir = parent
  }
  return null
}

const cliPath = findCli(process.cwd())
if (!cliPath) {
  console.error('Codacy CLI script not found (.codacy/cli.sh)')
  process.exit(1)
}

let buffer = ''
process.stdin.setEncoding('utf8')
process.stdin.on('data', chunk => {
  buffer += chunk
  let idx
  while ((idx = buffer.indexOf('\n')) !== -1) {
    const line = buffer.slice(0, idx).trim()
    buffer = buffer.slice(idx + 1)
    if (line) handleLine(line)
  }
})

process.stdin.on('end', () => process.exit(0))

function send(resultObj) {
  process.stdout.write(JSON.stringify(resultObj) + '\n')
}

function success(id, result) {
  send({ jsonrpc: JSONRPC_VERSION, id, result })
}

function failure(id, code, message, data) {
  send({ jsonrpc: JSONRPC_VERSION, id, error: { code, message, data } })
}

function runAnalyze(params, id) {
  const format = params?.format || 'sarif'
  const file = params?.file
  const args = ['analyze']
  if (file) args.push(file)
  args.push('--format', format)

  const proc = spawn(cliPath, args, { stdio: ['ignore', 'pipe', 'pipe'] })
  let stdout = ''
  let stderr = ''
  proc.stdout.on('data', d => { stdout += d.toString() })
  proc.stderr.on('data', d => { stderr += d.toString() })
  proc.on('close', code => {
    if (code !== 0) {
      failure(id, -32001, 'Codacy CLI analyze failed', { exitCode: code, stderr })
    } else {
      success(id, { sarif: stdout })
    }
  })
}

function handleLine(line) {
  let msg
  try {
    msg = JSON.parse(line)
  } catch (e) {
    return
  }
  const { id, method, params } = msg
  if (!method) return
  switch (method) {
    case 'initialize':
      success(id, { capabilities: { analyze: true } })
      break
    case 'shutdown':
      success(id, true)
      break
    case 'analyze':
      runAnalyze(params, id)
      break
    default:
      failure(id, -32601, `Method not implemented: ${method}`)
  }
}
