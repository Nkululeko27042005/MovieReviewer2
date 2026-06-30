import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from config import Config

class FileService:
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_file(file, folder, max_size_mb=5):
        """Save uploaded file with validation"""
        if not file or not file.filename:
            return None
        
        if not FileService.allowed_file(file.filename):
            raise ValueError('File type not allowed')
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{unique_id}.{extension}"
        
        # Ensure folder exists
        os.makedirs(folder, exist_ok=True)
        
        filepath = os.path.join(folder, filename)
        filepath = filepath.replace('\\', '/')
        
        # Save file
        file.save(filepath)
        
        # Optimize image
        FileService.optimize_image(filepath, max_size_mb)
        
        # Return relative path for database
        return filepath
    
    @staticmethod
    def save_multiple_files(files, folder, max_size_mb=5):
        """Save multiple uploaded files"""
        saved_paths = []
        for file in files:
            path = FileService.save_file(file, folder, max_size_mb)
            if path:
                saved_paths.append(path)
        return saved_paths
    
    @staticmethod
    def optimize_image(filepath, max_size_mb=5):
        """Optimize image size and quality"""
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                max_dimension = 2000
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Compress
                quality = 85
                img.save(filepath, 'JPEG', quality=quality, optimize=True)
        except Exception as e:
            print(f"Error optimizing image {filepath}: {e}")
    
    @staticmethod
    def delete_file(filepath):
        """Delete a file from the filesystem"""
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    
    @staticmethod
    def delete_multiple_files(filepaths):
        """Delete multiple files"""
        for filepath in filepaths:
            FileService.delete_file(filepath)
        return True
    
    @staticmethod
    def get_file_size(filepath):
        """Get file size in bytes"""
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    
    @staticmethod
    def get_url_path(filepath):
        """Convert filesystem path to URL path"""
        if filepath and filepath.startswith('app/'):
            return '/' + filepath.replace('app/', '', 1)
        return filepath