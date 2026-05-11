import { spawn, ChildProcess } from 'child_process'

interface PythonManagerOptions {
  port: number
  pythonPath: string
  projectPath: string
}

export class PythonManager {
  private process: ChildProcess | null = null
  private options: PythonManagerOptions
  private running = false

  constructor(options: PythonManagerOptions) {
    this.options = options
  }

  async start(): Promise<void> {
    const { port, pythonPath, projectPath } = this.options
    const modulePath = projectPath.replace(/\\/g, '/')

    return new Promise((resolve, reject) => {
      let resolved = false

      this.process = spawn(pythonPath, [
        '-m', 'uvicorn',
        'hermes.接口.应用:应用',
        '--host', '127.0.0.1',
        '--port', String(port),
        '--log-level', 'info'
      ], {
        cwd: modulePath,
        env: { ...process.env, PYTHONPATH: modulePath },
        stdio: ['ignore', 'pipe', 'pipe']
      })

      const onData = (data: Buffer) => {
        if (!resolved && data.toString().includes('Uvicorn running on')) {
          resolved = true
          this.running = true
          resolve()
        }
      }

      this.process.stdout?.on('data', onData)
      this.process.stderr?.on('data', onData)

      this.process.on('error', (err) => {
        resolved = true
        this.running = false
        reject(new Error(`Failed to start Python: ${err.message}`))
      })

      this.process.on('exit', (code) => {
        if (!resolved) {
          resolved = true
          this.running = false
          reject(new Error(`Python process exited with code ${code ?? 'unknown'} before starting`))
        }
      })

      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true
          reject(new Error('Python backend startup timeout (15s)'))
        }
      }, 15000)

      this.process.on('close', () => clearTimeout(timeout))
    })
  }

  async stop(): Promise<void> {
    if (this.process) {
      this.process.kill('SIGTERM')
      await new Promise((resolve) => setTimeout(resolve, 3000))
      if (this.process && !this.process.killed) {
        this.process.kill('SIGKILL')
      }
      this.running = false
    }
  }

  isRunning(): boolean {
    return this.running
  }

  getPort(): number {
    return this.options.port
  }
}
