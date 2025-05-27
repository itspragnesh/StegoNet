from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import torch
import torchvision.transforms as transforms
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import logging
from models import PreparationNetwork, HidingNetwork, RevealNetwork, tensor_to_pil, pil_to_bytes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize models with error handling
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
prep_net = None
hide_net = None
reveal_net = None
models_loaded = False
mock_mode = False  # Enable mock mode for testing without models

# Define constants for image normalization
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

# Supported image formats
SUPPORTED_FORMATS = {'PNG', 'JPEG', 'JPG'}

model_files = {
    "prep_net": "preparation_network.pth",
    "hide_net": "hiding_network.pth",
    "reveal_net": "reveal_network.pth"
}

def load_models():
    global prep_net, hide_net, reveal_net, models_loaded, mock_mode
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Checking for model files: {list(model_files.values())}")
    
    missing_files = [f for f in model_files.values() if not os.path.exists(f)]
    if missing_files:
        logger.warning(f"Missing model files: {missing_files}. Enabling mock mode for testing.")
        mock_mode = True
        return False

    try:
        prep_net = PreparationNetwork().to(device)
        hide_net = HidingNetwork().to(device)
        reveal_net = RevealNetwork().to(device)

        prep_net.load_state_dict(torch.load(model_files["prep_net"], map_location=device))
        hide_net.load_state_dict(torch.load(model_files["hide_net"], map_location=device))
        reveal_net.load_state_dict(torch.load(model_files["reveal_net"], map_location=device))
        prep_net.eval()
        hide_net.eval()
        reveal_net.eval()
        logger.info("Models loaded successfully.")
        models_loaded = True
        return True
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}. Enabling mock mode.")
        mock_mode = True
        return False

models_loaded = load_models()

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    stego_image BLOB)''')
    conn.commit()
    conn.close()

init_db()

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Registered successfully"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"message": "Login successful", "username": username}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username == "admin" and password == "admin":
        return jsonify({"message": "Admin login successful"}), 200
    return jsonify({"error": "Invalid admin credentials"}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = [user[0] for user in c.fetchall()]
    conn.close()
    return jsonify(users)

# Image processing routes
@app.route('/api/send-stego', methods=['POST'])
def send_stego():
    if not models_loaded and not mock_mode:
        logger.warning("Steganography models not loaded, returning 503")
        return jsonify({"error": "Steganography models are not loaded. Ensure .pth files are in the backend directory."}), 503

    sender = request.form.get('sender')
    receiver = request.form.get('receiver')
    cover_file = request.files.get('cover_image')
    secret_file = request.files.get('secret_image')

    if not all([sender, receiver, cover_file, secret_file]):
        logger.error(f"Missing required fields: sender={sender}, receiver={receiver}, cover_file={cover_file}, secret_file={secret_file}")
        return jsonify({"error": "Missing required fields: sender, receiver, cover_image, and secret_image are required"}), 400

    try:
        # Validate image files
        logger.info("Validating image files")
        cover_filename = cover_file.filename
        secret_filename = secret_file.filename
        cover_ext = cover_filename.rsplit('.', 1)[1].upper() if '.' in cover_filename else ''
        secret_ext = secret_filename.rsplit('.', 1)[1].upper() if '.' in secret_filename else ''
        
        if cover_ext not in SUPPORTED_FORMATS or secret_ext not in SUPPORTED_FORMATS:
            logger.error(f"Unsupported image format: cover={cover_ext}, secret={secret_ext}")
            return jsonify({"error": f"Unsupported image format. Supported formats are {SUPPORTED_FORMATS}"}), 400

        if mock_mode:
            logger.info("Mock mode: Returning dummy stego image")
            # Create a dummy image with a label
            dummy_image = Image.new('RGB', (256, 256), color='gray')
            draw = ImageDraw.Draw(dummy_image)
            try:
                font = ImageFont.load_default()
            except AttributeError:
                font = ImageFont.load_default()
            draw.text((10, 10), "Mock Stego Image\nModels Missing", fill="white", font=font)
            image_bytes = pil_to_bytes(dummy_image)
        else:
            logger.info("Opening cover and secret images")
            cover_image = Image.open(cover_file).convert("RGB")
            secret_image = Image.open(secret_file).convert("RGB")

            # Validate image dimensions
            cover_size = cover_image.size
            secret_size = secret_image.size
            logger.info(f"Cover image size: {cover_size}, Secret image size: {secret_size}")
            if cover_size[0] < 256 or cover_size[1] < 256 or secret_size[0] < 256 or secret_size[1] < 256:
                logger.error("Image dimensions too small")
                return jsonify({"error": "Images must be at least 256x256 pixels"}), 400

            logger.info("Setting up image transforms")
            transform = transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize(mean=MEAN, std=STD)
            ])

            logger.info("Transforming images to tensors")
            cover_tensor = transform(cover_image).unsqueeze(0).to(device)
            secret_tensor = transform(secret_image).unsqueeze(0).to(device)
            logger.info(f"Cover tensor shape: {cover_tensor.shape}, Secret tensor shape: {secret_tensor.shape}")

            if cover_tensor.shape != (1, 3, 256, 256) or secret_tensor.shape != (1, 3, 256, 256):
                logger.error(f"Invalid tensor shapes: cover={cover_tensor.shape}, secret={secret_tensor.shape}")
                return jsonify({"error": "Image tensors have invalid shapes. Expected (1, 3, 256, 256)"}), 500

            logger.info("Running PreparationNetwork")
            with torch.no_grad():
                prepared_secret = prep_net(secret_tensor)
                logger.info(f"Prepared secret shape: {prepared_secret.shape}")
                if prepared_secret.shape[1] != 65:  # Expected output channels from PreparationNetwork
                    logger.error(f"PreparationNetwork output shape mismatch: {prepared_secret.shape}")
                    return jsonify({"error": "PreparationNetwork output shape mismatch"}), 500

            logger.info("Running HidingNetwork")
            with torch.no_grad():
                # Combine cover_tensor and prepared_secret for HidingNetwork
                stego_image = hide_net(cover_tensor, prepared_secret)
                logger.info(f"Stego tensor shape: {stego_image.shape}")
                if stego_image.shape != (1, 3, 256, 256):
                    logger.error(f"HidingNetwork output shape mismatch: {stego_image.shape}")
                    return jsonify({"error": "HidingNetwork output shape mismatch. Expected (1, 3, 256, 256)"}), 500

            logger.info("Converting stego tensor to PIL image")
            stego_pil = tensor_to_pil(stego_image, MEAN, STD)
            logger.info("Converting stego image to bytes")
            image_bytes = pil_to_bytes(stego_pil)

        logger.info("Saving stego image to database")
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, receiver, stego_image) VALUES (?, ?, ?)", (sender, receiver, image_bytes))
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Stego image sent" + (" (mock mode - no models loaded)" if mock_mode else ""),
            "stego_image": base64.b64encode(image_bytes).decode('utf-8')
        }), 200
    except Exception as e:
        logger.error(f"Error processing stego image: {str(e)}")
        return jsonify({"error": f"Failed to process images: {str(e)}"}), 500

@app.route('/api/received-images/<username>', methods=['GET'])
def get_received_images(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, sender, stego_image FROM messages WHERE receiver=?", (username,))
    messages = c.fetchall()
    conn.close()
    result = [{"id": msg[0], "sender": msg[1], "stego_image": base64.b64encode(msg[2]).decode('utf-8')} for msg in messages]
    return jsonify(result)

@app.route('/api/extract-secret/<int:msg_id>', methods=['GET'])
def extract_secret(msg_id):
    if not models_loaded and not mock_mode:
        logger.warning("Steganography models not loaded, returning 503")
        return jsonify({"error": "Steganography models are not loaded. Ensure .pth files are in the backend directory."}), 503

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT stego_image FROM messages WHERE id=?", (msg_id,))
    img_blob = c.fetchone()
    conn.close()

    if not img_blob:
        logger.error(f"Image with ID {msg_id} not found")
        return jsonify({"error": "Image not found"}), 404

    try:
        if mock_mode:
            logger.info("Mock mode: Returning dummy secret image")
            dummy_image = Image.new('RGB', (256, 256), color='blue')
            draw = ImageDraw.Draw(dummy_image)
            try:
                font = ImageFont.load_default()
            except AttributeError:
                font = ImageFont.load_default()
            draw.text((10, 10), "Mock Secret Image\nModels Missing", fill="white", font=font)
            image_bytes = pil_to_bytes(dummy_image)
        else:
            logger.info("Opening stego image from database")
            image = Image.open(io.BytesIO(img_blob[0])).convert("RGB")

            logger.info("Setting up image transforms for extraction")
            transform = transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize(mean=MEAN, std=STD)
            ])

            logger.info("Transforming stego image to tensor")
            stego_tensor = transform(image).unsqueeze(0).to(device)
            logger.info(f"Stego tensor shape for extraction: {stego_tensor.shape}")

            if stego_tensor.shape != (1, 3, 256, 256):
                logger.error(f"Invalid stego tensor shape: {stego_tensor.shape}")
                return jsonify({"error": "Stego tensor has invalid shape. Expected (1, 3, 256, 256)"}), 500

            logger.info("Running RevealNetwork to extract secret image")
            with torch.no_grad():
                revealed_secret = reveal_net(stego_tensor)
                logger.info(f"Revealed secret shape: {revealed_secret.shape}")
                if revealed_secret.shape != (1, 3, 256, 256):
                    logger.error(f"RevealNetwork output shape mismatch: {revealed_secret.shape}")
                    return jsonify({"error": "RevealNetwork output shape mismatch. Expected (1, 3, 256, 256)"}), 500

            logger.info("Converting extracted secret to PIL image")
            revealed_pil = tensor_to_pil(revealed_secret, MEAN, STD)
            logger.info("Converting extracted secret image to bytes")
            image_bytes = pil_to_bytes(revealed_pil)

        return jsonify({
            "secret_image": base64.b64encode(image_bytes).decode('utf-8'),
            "message": "Secret image extracted" + (" (mock mode - no models loaded)" if mock_mode else "")
        })
    except Exception as e:
        logger.error(f"Error extracting secret image: {str(e)}")
        return jsonify({"error": f"Failed to extract secret: {str(e)}"}), 500

@app.route('/api/delete-image/<int:msg_id>', methods=['DELETE'])
def delete_image(msg_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    c.execute("DELETE FROM SQLITE_SEQUENCE WHERE name='messages'")
    conn.commit()
    conn.close()
    logger.info(f"Image with ID {msg_id} deleted")
    return jsonify({"message": "Image deleted successfully"}), 200

@app.route('/api/remove-user/<username>', methods=['DELETE'])
def remove_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    c.execute("DELETE FROM messages WHERE sender=? OR receiver=?", (username, username))
    conn.commit()
    conn.close()
    logger.info(f"User {username} removed")
    return jsonify({"message": f"User {username} removed"}), 200

@app.route('/api/all-messages', methods=['GET'])
def get_all_messages():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, sender, receiver FROM messages")
    messages = c.fetchall()
    conn.close()
    result = [{"id": msg[0], "sender": msg[1], "receiver": msg[2]} for msg in messages]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)