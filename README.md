# Vapi MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that integrates with [Vapi AI](https://vapi.ai) to trigger outbound phone calls. Deployable to Render with streamable HTTP transport.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/InteractionCo/mcp-server-template)

## Features

- **Make Vapi Calls**: Trigger outbound phone calls to any destination number
- **Fixed Source**: Uses your configured Vapi phone number and assistant
- **Detailed Responses**: Returns call ID, status, and error information
- **Poke Integration**: Connect to Poke for voice-activated phone calls

## Setup

### Environment Variables

Create a `.env.local` file (for local development) or configure these in your deployment:

```bash
VAPI_API_KEY=your_vapi_api_key_here
ANDY=your_assistant_id_here
PHONE=your_phone_id_here
```

### Local Development

Fork the repo, then run:

```bash
git clone <your-repo-url>
cd mcp-server-template
conda create -n vapi-mcp python=3.13
conda activate vapi-mcp
pip install -r requirements.txt
```

### Test Locally

```bash
python src/server.py
# then in another terminal run:
npx @modelcontextprotocol/inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using "Streamable HTTP" transport (NOTE THE `/mcp`!).

## Available Tools

### `make_vapi_call`

Triggers an outbound phone call using Vapi API.

**Parameters:**
- `destination_phone_number` (required): The phone number to call (e.g., "+1234567890")
- `customer_name` (optional): Name of the customer for context

**Response:**
```json
{
  "success": true,
  "call_id": "call_123456",
  "status": "queued",
  "message": "Call successfully initiated to +1234567890",
  "assistant_id": "your_assistant_id",
  "phone_id": "your_phone_id",
  "customer_number": "+1234567890",
  "customer_name": "John Doe"
}
```

## Deployment

### Option 1: One-Click Deploy
Click the "Deploy to Render" button above.

### Option 2: Manual Deployment
1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Add environment variables in Render dashboard:
   - `VAPI_API_KEY`
   - `ANDY`
   - `PHONE`
6. Render will automatically detect the `render.yaml` configuration

Your server will be available at `https://your-service-name.onrender.com/mcp` (NOTE THE `/mcp`!)

## Poke Integration

You can connect your MCP server to Poke at [poke.com/settings/connections](https://poke.com/settings/connections).

To test the connection, ask Poke something like:
```
Tell the subagent to use the "Vapi MCP" integration's "make_vapi_call" tool to call +1234567890
```

If you run into persistent issues with Poke not calling the right MCP (e.g., after renaming the connection), you may send `clearhistory` to Poke to delete all message history and start fresh.

## API Reference

The server makes calls to Vapi's API endpoint:
- **URL**: `https://api.vapi.ai/call/phone`
- **Method**: POST
- **Headers**: 
  - `Authorization: Bearer {VAPI_API_KEY}`
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "assistantId": "{ANDY}",
    "phoneNumberId": "{PHONE}",
    "customer": {
      "number": "{destination_phone_number}",
      "name": "{customer_name}" // optional
    }
  }
  ```
