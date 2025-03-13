from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import time
import logging
import traceback
import ai_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('app.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Log important configuration
logger.info("Starting LinkedIn Auto-Networker Backend")
if os.getenv("OPENROUTER_API_KEY"):
    logger.info("OpenRouter API key found")
else:
    logger.warning("OpenRouter API key not found - will use fallback messages")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Error handler for all routes
@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({
        "error": "Internal server error",
        "message": str(e)
    }), 500

# In-memory storage (would be replaced with a database in production)
profiles_data = {}
connection_history = []

# Rate limiting configuration
MAX_REQUESTS_PER_HOUR = int(os.getenv('MAX_REQUESTS_PER_HOUR', 20))
request_timestamps = []

def check_rate_limit():
    """Check if rate limit has been exceeded"""
    global request_timestamps
    
    # Current time
    current_time = time.time()
    
    # Remove timestamps older than 1 hour
    one_hour_ago = current_time - 3600
    request_timestamps = [ts for ts in request_timestamps if ts > one_hour_ago]
    
    # Check if at limit
    return len(request_timestamps) >= MAX_REQUESTS_PER_HOUR

def update_rate_limit():
    """Update rate limiting counters"""
    global request_timestamps
    
    # Add current timestamp
    request_timestamps.append(time.time())

@app.route('/')
def index():
    """Root endpoint - health check"""
    return jsonify({
        "status": "online",
        "service": "LinkedIn Auto-Networker Backend",
        "version": "1.0.0"
    })

@app.route('/api/status', methods=['GET'])
def status():
    """Health check endpoint with stats"""
    return jsonify({
        "status": "online",
        "profiles_collected": len(profiles_data),
        "connections_sent": len(connection_history),
        "timestamp": time.time()
    })

@app.route('/api/collect-profiles', methods=['POST'])
def collect_profiles():
    """Store profiles collected from LinkedIn"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    
    if not data or 'profiles' not in data:
        return jsonify({"error": "No profiles provided"}), 400
    
    # Process each profile
    for profile in data['profiles']:
        if 'profileUrl' in profile:
            # Store profile data using URL as unique key
            profiles_data[profile['profileUrl']] = profile
    
    return jsonify({
        "success": True,
        "profiles_count": len(profiles_data),
        "message": f"Stored {len(data['profiles'])} profiles"
    })

@app.route('/api/get-profiles', methods=['GET'])
def get_profiles():
    """Get collected profiles"""
    # Optional filtering by status
    status_filter = request.args.get('status')
    
    if status_filter:
        filtered_profiles = [p for p in profiles_data.values() 
                             if p.get('status') == status_filter]
        return jsonify({"profiles": filtered_profiles})
    
    # Return all profiles if no filter
    return jsonify({"profiles": list(profiles_data.values())})

@app.route('/api/record-connection', methods=['POST'])
def record_connection():
    """Record a successful connection"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    
    if not data or 'profileUrl' not in data:
        return jsonify({"error": "No profile URL provided"}), 400
    
    # Check rate limiting
    if check_rate_limit():
        logger.warning("Rate limit exceeded")
        return jsonify({
            "error": "Rate limit exceeded",
            "message": f"Maximum of {MAX_REQUESTS_PER_HOUR} connections per hour allowed"
        }), 429
    
    # Update rate limiting counter
    update_rate_limit()
    
    profile_url = data['profileUrl']
    logger.info(f"Recording connection for profile: {profile_url}")
    
    # Add to connection history
    connection_record = {
        "profileUrl": profile_url,
        "timestamp": data.get('timestamp', time.time()),
        "messageUsed": data.get('messageUsed', None)
    }
    
    connection_history.append(connection_record)
    
    # Update profile status if it exists in our data
    if profile_url in profiles_data:
        profiles_data[profile_url]['status'] = 'connected'
        profiles_data[profile_url]['connectionTimestamp'] = connection_record['timestamp']
    
    return jsonify({
        "success": True,
        "connections_count": len(connection_history),
        "message": "Connection recorded successfully"
    })

@app.route('/api/generate-message', methods=['POST'])
def generate_message():
    """Generate personalized message using AI"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    
    if not data or 'profileData' not in data:
        return jsonify({"error": "No profile data provided"}), 400
    
    profile_data = data['profileData']
    
    # Call the AI generator
    try:
        message = ai_generator.generate_message(profile_data)
        return jsonify({
            "success": True,
            "message": message
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "I came across your profile and would love to connect!"  # Fallback message
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=port)