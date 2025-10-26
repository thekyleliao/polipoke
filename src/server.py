#!/usr/bin/env python3
import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP("Vapi MCP Server")

@mcp.tool(description="Make an outbound phone call using Vapi API to a specified destination number")
def make_vapi_call(destination_phone_number: str, customer_name: str = None) -> dict:
    """
    Trigger an outbound phone call using Vapi API.
    
    Args:
        destination_phone_number: The phone number to call (e.g., "+1234567890")
        customer_name: Optional name of the customer for context
    
    Returns:
        dict: Detailed response including call status, ID, and any errors
    """
    try:
        # Load environment variables
        api_key = os.environ.get("VAPI_API_KEY")
        assistant_id = os.environ.get("ANDY")
        phone_id = os.environ.get("PHONE")
        
        # Validate required environment variables
        if not all([api_key, assistant_id, phone_id]):
            missing = []
            if not api_key: missing.append("VAPI_API_KEY")
            if not assistant_id: missing.append("ANDY")
            if not phone_id: missing.append("PHONE")
            
            return {
                "success": False,
                "error": f"Missing required environment variables: {', '.join(missing)}",
                "message": "Please configure all required environment variables"
            }
        
        # Prepare API request
        url = "https://api.vapi.ai/call/phone"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "assistantId": assistant_id,
            "phoneNumberId": phone_id,
            "customer": {
                "number": destination_phone_number
            }
        }
        
        # Add customer name if provided
        if customer_name:
            payload["customer"]["name"] = customer_name
        
        # Make API call
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30.0)
            
            if response.status_code == 200:
                call_data = response.json()
                return {
                    "success": True,
                    "call_id": call_data.get("id"),
                    "status": call_data.get("status"),
                    "message": f"Call successfully initiated to {destination_phone_number}",
                    "assistant_id": assistant_id,
                    "phone_id": phone_id,
                    "customer_number": destination_phone_number,
                    "customer_name": customer_name,
                    "raw_response": call_data
                }
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("message", error_detail)
                except:
                    pass
                
                return {
                    "success": False,
                    "error": f"Vapi API error (HTTP {response.status_code}): {error_detail}",
                    "message": f"Failed to initiate call to {destination_phone_number}",
                    "status_code": response.status_code
                }
                
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timeout - Vapi API did not respond in time",
            "message": "Call initiation timed out"
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "message": "Failed to connect to Vapi API"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "An unexpected error occurred while making the call"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting Vapi MCP Server on {host}:{port}")
    print("Available tools: make_vapi_call")
    
    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
