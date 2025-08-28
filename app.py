#!/usr/bin/env python3
"""
Photo Slideshow Web Application
Dual interface: TV Display + Admin Upload
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import os
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path
import mimetypes
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/photos'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Configuration
CONFIG_FILE = 'slideshow_config.json'
DEFAULT_CONFIG = {
    "slideshow": {
        "interval": 5000,
        "transition": "fade",
        "autoPlay": True,
        "loop": True,
        "random": False
    },
    "display": {
        "showControls": True,
        "showInfo": True,
        "fullscreen": True
    }
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_config():
    """Load configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def get_photos():
    """Get list of photos from upload folder"""
    photos = []
    photos_dir = Path(app.config['UPLOAD_FOLDER'])
    
    if photos_dir.exists():
        for file_path in photos_dir.glob("*"):
            if file_path.is_file() and allowed_file(file_path.name):
                # Get file info
                stat = file_path.stat()
                photos.append({
                    "id": len(photos),
                    "name": file_path.name,
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "url": f"/static/photos/{file_path.name}"
                })
    
    # Sort by modification time (newest first)
    photos.sort(key=lambda x: x['modified'], reverse=True)
    
    # Update IDs after sorting
    for i, photo in enumerate(photos):
        photo['id'] = i
    
    return photos

def create_upload_folder():
    """Create upload folder if it doesn't exist"""
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

@app.route('/')
def tv_display():
    """TV Display Interface - Clean slideshow for TV"""
    config = load_config()
    photos = get_photos()
    return render_template('tv_display.html', photos=photos, config=config)

@app.route('/admin')
def admin_panel():
    """Admin Panel - Photo management interface"""
    photos = get_photos()
    config = load_config()
    return render_template('admin_panel.html', photos=photos, config=config)

@app.route('/api/photos')
def api_photos():
    """API endpoint for photos"""
    photos = get_photos()
    return jsonify(photos)

@app.route('/api/config')
def api_config():
    """API endpoint for configuration"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json
        if save_config(new_config):
            # Emit real-time update to all connected clients
            socketio.emit('config_updated', new_config)
            return jsonify({"success": True, "message": "Configuration updated"})
        else:
            return jsonify({"success": False, "message": "Failed to save configuration"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_photo():
    """Handle photo upload"""
    try:
        if 'photo' not in request.files:
            return jsonify({"success": False, "message": "No file selected"}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            # Create upload folder
            upload_dir = create_upload_folder()
            
            # Secure filename and save
            filename = secure_filename(file.filename)
            timestamp = int(time.time())
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            file_path = upload_dir / unique_filename
            file.save(file_path)
            
            # Get photo info
            stat = file_path.stat()
            photo_info = {
                "id": len(get_photos()),
                "name": unique_filename,
                "filename": unique_filename,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "url": f"/static/photos/{unique_filename}"
            }
            
            # Emit real-time update to all connected clients
            socketio.emit('photo_added', photo_info)
            
            return jsonify({
                "success": True, 
                "message": "Photo uploaded successfully",
                "photo": photo_info
            })
        else:
            return jsonify({"success": False, "message": "File type not allowed"}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_photo(filename):
    """Delete a photo"""
    try:
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        
        if file_path.exists() and allowed_file(filename):
            file_path.unlink()
            
            # Emit real-time update to all connected clients
            socketio.emit('photo_deleted', {"filename": filename})
            
            return jsonify({"success": True, "message": "Photo deleted successfully"})
        else:
            return jsonify({"success": False, "message": "File not found or not allowed"}), 404
            
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reorder', methods=['POST'])
def reorder_photos():
    """Reorder photos"""
    try:
        new_order = request.json.get('order', [])
        
        # Update photo order (this could be stored in a database)
        # For now, we'll just acknowledge the request
        socketio.emit('photos_reordered', {"order": new_order})
        
        return jsonify({"success": True, "message": "Order updated"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    # Create upload folder
    create_upload_folder()
    
    # Load or create default config
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    
    print("=" * 60)
    print("📺 Photo Slideshow Web Application")
    print("=" * 60)
    print("🌐 TV Display: http://localhost:5000/")
    print("🔧 Admin Panel: http://localhost:5000/admin")
    print("📁 Photos folder:", app.config['UPLOAD_FOLDER'])
    print("=" * 60)
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
