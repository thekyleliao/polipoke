#!/usr/bin/env python3
import os
import httpx
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env.local file
load_dotenv('.env.local')

mcp = FastMCP("Vapi MCP Server")

@mcp.tool(description="Make an outbound phone call using Vapi API to a specified destination number")
def make_vapi_call(destination_phone_number: str, customer_name: Optional[str] = None) -> dict:
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
        
        # Make API call with extended timeout for Vapi processing
        with httpx.Client() as client:
            try:
                # Initial call initiation
                response = client.post(url, headers=headers, json=payload, timeout=60.0)
                
                if response.status_code == 200:
                    call_data = response.json()
                    call_id = call_data.get("id")
                    
                    # Wait a moment for Vapi to process the call details
                    import time
                    time.sleep(2)
                    
                    # Try to get updated call details if we have a call ID
                    call_details = None
                    if call_id:
                        try:
                            # Get call details with additional timeout
                            details_response = client.get(
                                f"https://api.vapi.ai/call/{call_id}",
                                headers={"Authorization": f"Bearer {api_key}"},
                                timeout=30.0
                            )
                            if details_response.status_code == 200:
                                call_details = details_response.json()
                        except Exception as e:
                            # If getting details fails, we still have the initial response
                            print(f"Warning: Could not fetch call details: {e}")
                    
                    # Use detailed response if available, otherwise use initial response
                    final_data = call_details if call_details else call_data
                    
                    return {
                        "success": True,
                        "call_id": call_id,
                        "status": final_data.get("status", "unknown"),
                        "message": f"Call successfully initiated to {destination_phone_number}",
                        "assistant_id": assistant_id,
                        "phone_id": phone_id,
                        "customer_number": destination_phone_number,
                        "customer_name": customer_name,
                        "call_duration": final_data.get("duration"),
                        "call_started_at": final_data.get("startedAt"),
                        "call_ended_at": final_data.get("endedAt"),
                        "transcript": final_data.get("transcript"),
                        "cost": final_data.get("cost"),
                        "raw_response": final_data
                    }
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("message", error_detail)
                        error_code = error_json.get("code", "unknown")
                    except:
                        error_code = "parse_error"
                    
                    return {
                        "success": False,
                        "error": f"Vapi API error (HTTP {response.status_code}): {error_detail}",
                        "error_code": error_code,
                        "message": f"Failed to initiate call to {destination_phone_number}",
                        "status_code": response.status_code,
                        "assistant_id": assistant_id,
                        "phone_id": phone_id,
                        "customer_number": destination_phone_number
                    }
                    
            except httpx.TimeoutException as e:
                return {
                    "success": False,
                    "error": f"Request timeout after 60 seconds: {str(e)}",
                    "message": "Call initiation timed out - Vapi may still be processing",
                    "timeout_seconds": 60,
                    "customer_number": destination_phone_number
                }
                
    except httpx.TimeoutException as e:
        return {
            "success": False,
            "error": f"Request timeout: {str(e)}",
            "message": "Call initiation timed out - Vapi may still be processing the call",
            "timeout_seconds": 60,
            "customer_number": destination_phone_number,
            "suggestion": "Check Vapi dashboard for call status"
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "message": "Failed to connect to Vapi API - check your internet connection",
            "customer_number": destination_phone_number,
            "suggestion": "Retry the call or check Vapi service status"
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {str(e)}",
            "message": f"Vapi API returned an error status: {e.response.status_code}",
            "status_code": e.response.status_code,
            "customer_number": destination_phone_number,
            "suggestion": "Check your API key and account status"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "An unexpected error occurred while making the call",
            "customer_number": destination_phone_number,
            "error_type": type(e).__name__,
            "suggestion": "Check server logs for more details"
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
