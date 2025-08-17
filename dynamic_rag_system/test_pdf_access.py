#!/usr/bin/env python3
"""
Test PDF file accessibility and basic processing
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_pdf_files():
    """Test PDF file access"""
    pdf_directory = '/Users/umangagarwal/Downloads/iesc1dd/'
    
    pdf_files = [
        'iesc1an.pdf', 'iesc1ps.pdf', 'iesc101.pdf', 'iesc102.pdf',
        'iesc103.pdf', 'iesc104.pdf', 'iesc105.pdf', 'iesc106.pdf', 
        'iesc107.pdf', 'iesc108.pdf', 'iesc109.pdf', 'iesc110.pdf',
        'iesc111.pdf', 'iesc112.pdf'
    ]
    
    print("🔍 Testing PDF file accessibility...")
    
    available_files = []
    
    for filename in pdf_files:
        file_path = os.path.join(pdf_directory, filename)
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            available_files.append((filename, file_path, file_size))
            print(f"✅ {filename} - {file_size:.1f} MB")
        else:
            print(f"❌ {filename} - Not found")
    
    print(f"\n📊 Summary: {len(available_files)}/{len(pdf_files)} files available")
    
    if available_files:
        print("\n🧪 Testing PyMuPDF import...")
        try:
            import fitz
            print("✅ PyMuPDF imported successfully")
            
            # Test opening first available file
            first_file = available_files[0]
            print(f"\n📖 Testing PDF opening: {first_file[0]}")
            
            try:
                doc = fitz.open(first_file[1])
                print(f"✅ PDF opened successfully")
                print(f"   Pages: {doc.page_count}")
                
                # Test text extraction from first page
                if doc.page_count > 0:
                    page = doc[0]
                    text = page.get_text()
                    print(f"   First page text length: {len(text)} characters")
                    print(f"   Preview: {text[:100]}...")
                
                doc.close()
                return True
                
            except Exception as e:
                print(f"❌ Error opening PDF: {e}")
                return False
                
        except ImportError as e:
            print(f"❌ PyMuPDF import failed: {e}")
            return False
    
    return False

if __name__ == "__main__":
    test_pdf_files()