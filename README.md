# Vapi MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that integrates with [Vapi AI](https://vapi.ai) to trigger outbound phone calls. Deployable to railway with streamable HTTP transport.

[![Deploy to railway](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/InteractionCo/mcp-server-template)

## Features

- **Make Vapi Calls**: Trigger outbound phone calls to any destination number
- **Dual Assistant Support**: Choose between Andy or Mam assistant for calls
- **Fixed Source**: Uses your configured Vapi phone number and selected assistant
- **Detailed Responses**: Returns call ID, status, transcript, duration, and cost information
- **Poke Integration**: Connect to Poke for voice-activated phone calls
- **Enhanced Error Handling**: Comprehensive error messages with troubleshooting suggestions
- **Extended Timeouts**: Handles Vapi's processing time with up to 90+ second timeouts

## Setup

### Environment Variables

Create a `.env.local` file (for local development) or configure these in your deployment:

```bash
VAPI_API_KEY=your_vapi_api_key_here
ANDY=your_andy_assistant_id_here
MAM=your_mam_assistant_id_here
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

## How It Works

This MCP server integrates with [Vapi AI](https://vapi.ai) to make outbound phone calls through your configured assistant and phone number. Here's the flow:

1. **Tool Call**: Poke or another MCP client calls the `make_vapi_call` tool
2. **API Request**: Server sends a POST request to Vapi's API with call details
3. **Call Initiation**: Vapi processes the request and starts the outbound call
4. **Enhanced Response**: Server waits for Vapi to process, then fetches detailed call information
5. **Rich Data**: Returns comprehensive call details including transcript, duration, and cost

### Important Phone Number Format

**⚠️ Always include country code in phone numbers!**

- ✅ **Correct**: `+1234567890` (US), `+447700900123` (UK), `+33123456789` (France)
- ❌ **Incorrect**: `1234567890`, `07700900123`, `0123456789`

The `+` prefix is required for international format. Without it, Vapi may not be able to route the call properly.

## Available Tools

### `make_vapi_call`

Triggers an outbound phone call using Vapi API.

**Parameters:**
- `destination_phone_number` (required): The phone number to call **with country code** (e.g., "+1234567890")
- `customer_name` (optional): Name of the customer for context
- `assistant` (optional): Assistant to use for the call ("andy" or "mam", defaults to "andy")

**Enhanced Response:**
```json
{
  "success": true,
  "call_id": "call_123456",
  "status": "completed",
  "message": "Call successfully initiated to +1234567890 using Andy assistant",
  "assistant_used": "andy",
  "assistant_id": "your_assistant_id",
  "phone_id": "your_phone_id",
  "customer_number": "+1234567890",
  "customer_name": "John Doe",
  "call_duration": 45,
  "call_started_at": "2024-01-01T10:00:00Z",
  "call_ended_at": "2024-01-01T10:00:45Z",
  "transcript": "Hello, this is Andy from our company...",
  "cost": 0.15,
  "raw_response": { /* Full Vapi API response */ }
}
```

**Error Response Example:**
```json
{
  "success": false,
  "error": "Vapi API error (HTTP 400): Invalid phone number format",
  "error_type": "api_error",
  "error_code": "invalid_phone",
  "message": "Failed to initiate call to 1234567890 using Andy assistant",
  "status_code": 400,
  "assistant_requested": "andy",
  "suggestion": "Use international format with country code (e.g., +1234567890)"
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

### Option 3: Using Render CLI

If you prefer command line:

```bash
# Install Render CLI (choose one method)
# Option 1: Homebrew (macOS/Linux)
brew install render

# Option 2: Download from GitHub releases
# Visit: https://github.com/render/render-cli/releases

# Login to Render
render login

# List your services to find the service ID
render services list

# Set environment variables (replace SERVICE_ID with your actual service ID)
render services env set --service-id <SERVICE_ID> --key VAPI_API_KEY --value 19ca13e0-2ccd-4ad5-bee4-5101d59d08f0
render services env set --service-id <SERVICE_ID> --key ANDY --value cde00b8a-3ebf-4d4f-8587-7e8fec8e5fda
render services env set --service-id <SERVICE_ID> --key MAM --value your_mam_assistant_id_here
render services env set --service-id <SERVICE_ID> --key PHONE --value 9b27907e-7ea3-4b4a-9c78-fc2bcf5379b9

# Alternative: Bulk set from .env file
render services env set --service-id <SERVICE_ID> --env-file .env.local
```

## Poke Integration

You can connect your MCP server to Poke at [poke.com/settings/connections](https://poke.com/settings/connections).

### Example Usage in Poke

**Basic call (using Andy assistant):**
```
Tell the subagent to use the "Vapi MCP" integration's "make_vapi_call" tool to call +1234567890
```

**Call with customer name:**
```
Tell the subagent to use the "Vapi MCP" integration's "make_vapi_call" tool to call +1234567890 for customer John Smith
```

**Call using Mam assistant:**
```
Tell the subagent to use the "Vapi MCP" integration's "make_vapi_call" tool to call +1234567890 using Mam assistant
```

**Voice command example:**
```
"Hey Poke, call +1234567890 using the Vapi integration with Mam assistant"
```

### Troubleshooting

**Common Issues:**

1. **"Missing environment variables" error:**
   - Ensure `.env.local` file exists with all required variables
   - Check that `VAPI_API_KEY`, `ANDY`, `MAM`, and `PHONE` are set correctly

2. **"Invalid phone number format" error:**
   - Always use international format with country code: `+1234567890`
   - Never use local format: `1234567890`

3. **"Request timeout" error:**
   - Vapi may take up to 90 seconds to process calls
   - This is normal - check Vapi dashboard for call status

4. **Poke not calling the right MCP:**
   - Send `clearhistory` to Poke to reset connection
   - Verify connection name matches in Poke settings

5. **Connection refused errors:**
   - Ensure server is running: `python3 src/server.py`
   - Check that port 8000 is available
   - Verify MCP Inspector can connect to `http://localhost:8000/mcp`

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
