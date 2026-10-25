# DevPilot AI CLI

A command-line interface for interacting with the local DevPilot AI coding agent.

## Requirements

- Node.js 20 or newer
- DevPilot AI FastAPI service running locally

## Start the API

From the DevPilot AI repository root, open a separate terminal:

```powershell
cd .\ai-services
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check that the API is healthy:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Run the CLI locally

From the `cli` directory:

```powershell
node .\src\index.js --help
node .\src\index.js doctor
node .\src\index.js run "Explain this repository" --workspace "C:\Users\soham\Devpilot-ai"
```

## Commands

- `devpilot doctor` — check API connectivity.
- `devpilot run "<message>"` — send a task to the agent.
- `devpilot proposal <relative-file-path> <content-file>` — create a file-change proposal.
- `devpilot approve <proposal-id>` — apply a pending proposal.
- `devpilot reject <proposal-id>` — reject a pending proposal.

Set a different API URL with `--url` or the `DEVPILOT_URL` environment variable. The default is `http://127.0.0.1:8000`.

## Change safety

Creating a proposal does not itself apply the proposed file contents. Review the displayed diff before approving. Approval writes the proposed content to the target file.

Proposal state is currently held in the API process memory. Pending proposals may be lost if the API restarts.

## Development

Run the CLI test suite:

```powershell
npm test
```

## License

MIT
