#!/usr/bin/env python3
import os
import httpx
import logging
import asyncio
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env.local file
load_dotenv('.env.local')

mcp = FastMCP("Vapi MCP Server")

@mcp.tool(description="Health check endpoint to verify server is running")
def health_check() -> dict:
    """
    Simple health check to verify the server is operational.
    
    Returns:
        dict: Health status information
    """
    try:
        return {
            "status": "healthy",
            "message": "Vapi MCP Server is operational",
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }

@mcp.tool(description="Simple test tool to verify MCP connection")
def test_connection() -> dict:
    """
    Simple test tool to verify MCP connection is working.
    
    Returns:
        dict: Test response
    """
    return {
        "success": True,
        "message": "MCP connection is working",
        "server": "Vapi MCP Server",
        "tools_available": ["health_check", "test_connection", "make_vapi_call"]
    }

@mcp.tool(description="Make an outbound phone call using Vapi API to a specified destination number with either Andy or Mam assistant")
def make_vapi_call(destination_phone_number: str, customer_name: Optional[str] = None, assistant: str = "andy") -> dict:
    """
    Make an outbound phone call using Vapi API to a specified destination number with either Andy or Mam assistant.
    
    Args:
        destination_phone_number: The phone number to call (e.g., "+1234567890")
        customer_name: Optional name of the customer for context
        assistant: Assistant to use for the call ("andy" or "mam", defaults to "andy")
    
    Returns:
        dict: Detailed response including call status, ID, and any errors
    """
    try:
        # Validate assistant parameter
        if assistant.lower() not in ["andy", "mam"]:
            return {
                "success": False,
                "error": f"Invalid assistant '{assistant}'. Must be 'andy' or 'mam'",
                "error_type": "validation_error",
                "message": "Assistant parameter must be either 'andy' or 'mam'",
                "valid_options": ["andy", "mam"]
            }
        
        # Load environment variables
        api_key = os.environ.get("VAPI_API_KEY")
        andy_id = os.environ.get("ANDY")
        mam_id = os.environ.get("MAM")
        phone_id = os.environ.get("PHONE")
        
        # Get the correct assistant ID based on selection
        assistant_id = andy_id if assistant.lower() == "andy" else mam_id
        
        # Validate required environment variables
        missing_vars = []
        if not api_key: missing_vars.append("VAPI_API_KEY")
        if not assistant_id: missing_vars.append(f"{assistant.upper()}")
        if not phone_id: missing_vars.append("PHONE")
        
        if missing_vars:
            return {
                "success": False,
                "error": f"Missing required environment variables: {', '.join(missing_vars)}",
                "error_type": "configuration_error",
                "message": "Please configure all required environment variables",
                "missing_variables": missing_vars,
                "assistant_requested": assistant
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
                            logger.warning(f"Could not fetch call details: {e}")
                    
                    # Use detailed response if available, otherwise use initial response
                    final_data = call_details if call_details else call_data
                    
                    return {
                        "success": True,
                        "call_id": call_id,
                        "status": final_data.get("status", "unknown"),
                        "message": f"Call successfully initiated to {destination_phone_number} using {assistant.title()} assistant",
                        "assistant_used": assistant,
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
                    error_code = "unknown"
                    error_type = "api_error"
                    
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("message", error_detail)
                        error_code = error_json.get("code", "unknown")
                    except:
                        error_code = "parse_error"
                    
                    # Categorize error types based on status code
                    if response.status_code == 401:
                        error_type = "authentication_error"
                        suggestion = "Check your VAPI_API_KEY is correct and active"
                    elif response.status_code == 403:
                        error_type = "authorization_error"
                        suggestion = "Check your account permissions and assistant/phone access"
                    elif response.status_code == 429:
                        error_type = "rate_limit_error"
                        suggestion = "Too many requests - wait before retrying"
                    elif response.status_code >= 500:
                        error_type = "server_error"
                        suggestion = "Vapi service is experiencing issues - try again later"
                    else:
                        suggestion = "Check your request parameters and try again"
                    
                    return {
                        "success": False,
                        "error": f"Vapi API error (HTTP {response.status_code}): {error_detail}",
                        "error_type": error_type,
                        "error_code": error_code,
                        "message": f"Failed to initiate call to {destination_phone_number} using {assistant.title()} assistant",
                        "status_code": response.status_code,
                        "assistant_requested": assistant,
                        "assistant_id": assistant_id,
                        "phone_id": phone_id,
                        "customer_number": destination_phone_number,
                        "suggestion": suggestion
                    }
                    
            except httpx.TimeoutException as e:
                logger.error(f"Request timeout: {e}")
                return {
                    "success": False,
                    "error": f"Request timeout after 60 seconds: {str(e)}",
                    "error_type": "timeout_error",
                    "message": f"Call initiation timed out for {destination_phone_number} using {assistant.title()} assistant - Vapi may still be processing",
                    "timeout_seconds": 60,
                    "assistant_requested": assistant,
                    "customer_number": destination_phone_number,
                    "suggestion": "Check Vapi dashboard for call status or retry with a longer timeout"
                }
                
    except httpx.TimeoutException as e:
        logger.error(f"Timeout exception: {e}")
        return {
            "success": False,
            "error": f"Request timeout: {str(e)}",
            "error_type": "timeout_error",
            "message": f"Call initiation timed out for {destination_phone_number} using {assistant.title()} assistant - Vapi may still be processing the call",
            "timeout_seconds": 60,
            "assistant_requested": assistant,
            "customer_number": destination_phone_number,
            "suggestion": "Check Vapi dashboard for call status or retry the call"
        }
    except httpx.RequestError as e:
        logger.error(f"Network error: {e}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "error_type": "network_error",
            "message": f"Failed to connect to Vapi API for {destination_phone_number} using {assistant.title()} assistant - check your internet connection",
            "assistant_requested": assistant,
            "customer_number": destination_phone_number,
            "suggestion": "Retry the call or check Vapi service status and your network connection"
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error: {e}")
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {str(e)}",
            "error_type": "http_error",
            "message": f"Vapi API returned an error status {e.response.status_code} for {destination_phone_number} using {assistant.title()} assistant",
            "status_code": e.response.status_code,
            "assistant_requested": assistant,
            "customer_number": destination_phone_number,
            "suggestion": "Check your API key and account status, or contact Vapi support"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unexpected_error",
            "message": f"An unexpected error occurred while making call to {destination_phone_number} using {assistant.title()} assistant",
            "assistant_requested": assistant,
            "customer_number": destination_phone_number,
            "error_type_class": type(e).__name__,
            "suggestion": "Check server logs for more details or contact support"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting Vapi MCP Server on {host}:{port}")
    print("Available tools: health_check, test_connection, make_vapi_call")
    
    # Validate configuration at startup
    try:
        logger.info("Validating configuration...")
        api_key = os.environ.get("VAPI_API_KEY")
        andy_id = os.environ.get("ANDY")
        mam_id = os.environ.get("MAM")
        phone_id = os.environ.get("PHONE")
        
        missing = []
        if not api_key: missing.append("VAPI_API_KEY")
        if not andy_id: missing.append("ANDY")
        if not mam_id: missing.append("MAM")
        if not phone_id: missing.append("PHONE")
        
        if missing:
            logger.warning(f"Missing environment variables: {', '.join(missing)}")
        else:
            logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation error: {e}")
    
    try:
        logger.info("Starting MCP server...")
        mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
