from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from ..user_auth.authentication import IsAuthenticatedCustom, decode_refresh_token
from ..user_auth.permission import JWTAuthentication
from .serializers import QuerySerializer, ResponseSerializer
from .client.client import ExpenseMCPClient

@method_decorator(csrf_exempt, name='dispatch')
class AgentAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def post(self, request):
        try:
            # Get user ID from token
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'message': "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
            
            user_id = decode_refresh_token(refresh_token)

            # Validate input
            input_serializer = QuerySerializer(data=request.data)
            if not input_serializer.is_valid():
                return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Extract data from request
            query_data = input_serializer.validated_data
            query_data['user_id'] = user_id  # Add user ID to the data

            # Add additional context if provided
            if 'table_id' in request.data:
                query_data['table_id'] = request.data['table_id']
            if 'context_type' in request.data:
                query_data['context_type'] = request.data['context_type']

            # Run agent and get response
            response_obj = async_to_sync(self.run_agent_simple)(query_data)
            
            # Process and clean the response
            cleaned_response = self._clean_response(response_obj)
            
            return Response(cleaned_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def run_agent_simple(self, query_data):
        """Simplified agent runner that returns raw response."""
        try:
            return await ExpenseMCPClient.create_and_run_query(query_data)
        except Exception as e:
            return {"error": str(e)}

    def get(self, request):
        """Handle GET requests for basic status information."""
        try:
            # Get user ID from token
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'message': "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
            
            user_id = decode_refresh_token(refresh_token)
            
            return Response({
                "user_id": user_id,
                "status": "active"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _clean_response(self, response_obj):
        """Clean the response by removing step prefixes and extracting tool information."""
        import re
        
        # Initialize the cleaned response structure
        cleaned_response = {
            "response": "",
            "tools_called": []
        }
        
        # Extract the main response text
        if isinstance(response_obj, dict):
            if 'response' in response_obj:
                response_text = str(response_obj['response'])
            elif 'message' in response_obj:
                response_text = str(response_obj['message'])
            else:
                response_text = str(response_obj)
            
            # Extract tools information if available
            if 'raw_response' in response_obj:
                cleaned_response['tools_called'] = self._extract_tools_from_raw_response(response_obj['raw_response'])
        else:
            response_text = str(response_obj)
        
        # Remove step prefixes (Step 1:, Step 2:, etc.) from the beginning
        response_text = re.sub(r'^Step \d+:\s*[^\n]*\n?', '', response_text, flags=re.MULTILINE)
        
        # Also remove any remaining step patterns that might be at the start
        response_text = re.sub(r'^Step \d+.*?\n', '', response_text)
        
        # Clean up extra whitespace and newlines
        response_text = response_text.strip()
        
        cleaned_response['response'] = response_text
        
        return cleaned_response
    
    def _extract_tools_from_raw_response(self, raw_response):
        """Extract tool information from raw response."""
        tools_called = []
        
        try:
            if isinstance(raw_response, dict) and 'messages' in raw_response:
                messages = raw_response['messages']
                
                for message in messages:
                    if isinstance(message, list) and len(message) > 9:
                        # Check if this is an AI message with tool calls
                        if len(message) > 5 and message[5][1] == "ai":
                            # Look for tool calls in the message
                            if len(message) > 9 and message[9][0] == "tool_calls":
                                tool_calls = message[9][1]
                                
                                for tool_call in tool_calls:
                                    if isinstance(tool_call, dict) and 'name' in tool_call:
                                        tool_info = {
                                            'name': tool_call['name'],
                                            'args': tool_call.get('args', {})
                                        }
                                        tools_called.append(tool_info)
        except Exception:
            # If we can't extract tools, just return empty list
            pass
        
        return tools_called


@method_decorator(csrf_exempt, name='dispatch')
class AgentHistoryAPIView(APIView):
    """Simple endpoint for operation history."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request):
        """Get operation history."""
        try:
            # Get user ID from token
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'message': "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
            
            user_id = decode_refresh_token(refresh_token)
            
            return Response({
                "user_id": user_id,
                "history": []
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class AgentStreamingAPIView(APIView):
    """Simple streaming endpoint that returns unformatted responses."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedCustom]

    def post(self, request):
        """Handle requests with simple response."""
        try:
            # Get user ID from token
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'message': "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
            
            user_id = decode_refresh_token(refresh_token)

            # Validate input
            input_serializer = QuerySerializer(data=request.data)
            if not input_serializer.is_valid():
                return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Extract data from request
            query_data = input_serializer.validated_data
            query_data['user_id'] = user_id

            # Add context if provided
            if 'table_id' in request.data:
                query_data['table_id'] = request.data['table_id']
            if 'context_type' in request.data:
                query_data['context_type'] = request.data['context_type']
            
            # Run agent and return simple response
            response_obj = async_to_sync(self._run_agent)(query_data)
            
            # Process and clean the response
            cleaned_response = self._clean_response(response_obj)
            
            return Response(cleaned_response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def _run_agent(self, query_data):
        """Run agent with simple response."""
        try:
            return await ExpenseMCPClient.create_and_run_query(query_data)
        except Exception as e:
            return {"error": str(e)}

    def _clean_response(self, response_obj):
        """Clean the response by removing step prefixes and extracting tool information."""
        import re
        
        # Initialize the cleaned response structure
        cleaned_response = {
            "response": "",
            "tools_called": []
        }
        
        # Extract the main response text
        if isinstance(response_obj, dict):
            if 'response' in response_obj:
                response_text = str(response_obj['response'])
            elif 'message' in response_obj:
                response_text = str(response_obj['message'])
            else:
                response_text = str(response_obj)
            
            # Extract tools information if available
            if 'raw_response' in response_obj:
                cleaned_response['tools_called'] = self._extract_tools_from_raw_response(response_obj['raw_response'])
        else:
            response_text = str(response_obj)
        
        # Remove step prefixes (Step 1:, Step 2:, etc.) from the beginning
        response_text = re.sub(r'^Step \d+:\s*[^\n]*\n?', '', response_text, flags=re.MULTILINE)
        
        # Also remove any remaining step patterns that might be at the start
        response_text = re.sub(r'^Step \d+.*?\n', '', response_text)
        
        # Clean up extra whitespace and newlines
        response_text = response_text.strip()
        
        cleaned_response['response'] = response_text
        
        return cleaned_response
    
    def _extract_tools_from_raw_response(self, raw_response):
        """Extract tool information from raw response."""
        tools_called = []
        
        try:
            if isinstance(raw_response, dict) and 'messages' in raw_response:
                messages = raw_response['messages']
                
                for message in messages:
                    if isinstance(message, list) and len(message) > 9:
                        # Check if this is an AI message with tool calls
                        if len(message) > 5 and message[5][1] == "ai":
                            # Look for tool calls in the message
                            if len(message) > 9 and message[9][0] == "tool_calls":
                                tool_calls = message[9][1]
                                
                                for tool_call in tool_calls:
                                    if isinstance(tool_call, dict) and 'name' in tool_call:
                                        tool_info = {
                                            'name': tool_call['name'],
                                            'args': tool_call.get('args', {})
                                        }
                                        tools_called.append(tool_info)
        except Exception:
            # If we can't extract tools, just return empty list
            pass
        
        return tools_called
