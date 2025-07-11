#!/usr/bin/env python3
"""
Fix Multimodal Image Processing Issues
====================================

This script fixes the colorspace issues in multimodal citation service
that prevent visual citations from being extracted properly.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import os
import re
from pathlib import Path

def fix_image_extraction_methods():
    """Fix all image extraction methods in multimodal citation service"""
    
    service_path = Path("backend/services/multimodal_citation_service.py")
    
    if not service_path.exists():
        print(f"❌ File not found: {service_path}")
        return False
    
    # Read the current file
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Improved pixmap to PNG conversion with proper colorspace handling
    old_pixmap_pattern = r'''# Extract specific page content
        """
        try:
            doc = fitz\.open\(str\(doc_path\)\)
            
            if page_number <= len\(doc\):
                page = doc\[page_number - 1\]  # Convert to 0-based index
                
                # Render page as image
                pix = page\.get_pixmap\(matrix=fitz\.Matrix\(2, 2\)\)  # 2x scale for better quality
                img_data = pix\.tobytes\("png"\)'''
    
    new_pixmap_extraction = '''# Extract specific page content
        """
        try:
            doc = fitz.open(str(doc_path))
            
            if page_number <= len(doc):
                page = doc[page_number - 1]  # Convert to 0-based index
                
                # Render page as image with proper colorspace handling
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better quality
                
                # Handle colorspace conversion properly
                if pix.n > 4:  # CMYK colorspace
                    pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                    img_data = pix_rgb.tobytes("png")
                    pix_rgb = None
                    pix = None
                else:  # RGB or grayscale
                    img_data = pix.tobytes("png")
                    pix = None'''
    
    # Fix 2: Image extraction method for diagrams/tables
    old_image_extraction = r'''try:
            # Convert image to bytes
            if pix\.n < 5:  # Not CMYK
                img_data = pix\.tobytes\("png"\)
            else:  # CMYK, convert to RGB
                pix1 = fitz\.Pixmap\(fitz\.csRGB, pix\)
                img_data = pix1\.tobytes\("png"\)
                pix1 = None
            
            pix = None
            return img_data
            
        except Exception as e:
            logger\.error\(f"Image extraction failed: \{e\}"\)
            return None'''
    
    new_image_extraction = '''try:
            # Convert image to bytes with improved colorspace handling
            if pix.n <= 4:  # RGB or grayscale
                img_data = pix.tobytes("png")
            else:  # CMYK or other colorspaces, convert to RGB
                try:
                    pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                    img_data = pix_rgb.tobytes("png")
                    pix_rgb = None
                except Exception as colorspace_error:
                    logger.warning(f"Colorspace conversion failed: {colorspace_error}, using original")
                    # Fallback: try to extract as JPEG which handles CMYK better
                    try:
                        img_data = pix.tobytes("jpeg")
                    except:
                        logger.error("Both PNG and JPEG extraction failed")
                        return None
            
            pix = None
            return img_data
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return None'''
    
    # Fix 3: Table extraction method
    old_table_extraction = r'''try:
            if table_info:
                # Crop page to table area
                bbox = table_info\["bbox"\]
                rect = fitz\.Rect\(bbox\)
                pix = page\.get_pixmap\(matrix=fitz\.Matrix\(2, 2\), clip=rect\)
            else:
                # Full page if no specific table area
                pix = page\.get_pixmap\(matrix=fitz\.Matrix\(2, 2\)\)
            
            img_data = pix\.tobytes\("png"\)
            return img_data'''
    
    new_table_extraction = '''try:
            if table_info:
                # Crop page to table area
                bbox = table_info["bbox"]
                rect = fitz.Rect(bbox)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect)
            else:
                # Full page if no specific table area
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Handle colorspace properly for tables
            if pix.n > 4:  # CMYK
                pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix_rgb.tobytes("png")
                pix_rgb = None
            else:
                img_data = pix.tobytes("png")
            
            pix = None
            return img_data'''
    
    # Fix 4: Page section extraction
    old_section_extraction = r'''try:
            # For now, just return the full page
            # TODO: Implement text highlighting
            pix = page\.get_pixmap\(matrix=fitz\.Matrix\(2, 2\)\)
            img_data = pix\.tobytes\("png"\)
            return img_data'''
    
    new_section_extraction = '''try:
            # For now, just return the full page
            # TODO: Implement text highlighting
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Handle colorspace for page sections
            if pix.n > 4:  # CMYK
                pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix_rgb.tobytes("png")
                pix_rgb = None
            else:
                img_data = pix.tobytes("png")
            
            pix = None
            return img_data'''
    
    # Fix 5: Safety warning image extraction
    old_safety_extraction = r'''# Extract text section as image
                        page_img = page\.get_pixmap\(matrix=fitz\.Matrix\(2, 2\)\)\.tobytes\("png"\)'''
    
    new_safety_extraction = '''# Extract text section as image with proper colorspace handling
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        if pix.n > 4:  # CMYK
                            pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                            page_img = pix_rgb.tobytes("png")
                            pix_rgb = None
                        else:
                            page_img = pix.tobytes("png")
                        pix = None'''
    
    # Apply fixes
    fixes_applied = 0
    
    # Apply fix 1
    if re.search(old_pixmap_pattern, content, re.DOTALL):
        content = re.sub(old_pixmap_pattern, new_pixmap_extraction, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✅ Fixed pixmap extraction method")
    
    # Apply fix 2  
    if re.search(old_image_extraction, content, re.DOTALL):
        content = re.sub(old_image_extraction, new_image_extraction, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✅ Fixed image extraction method")
    
    # Apply fix 3
    if re.search(old_table_extraction, content, re.DOTALL):
        content = re.sub(old_table_extraction, new_table_extraction, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✅ Fixed table extraction method")
    
    # Apply fix 4
    if re.search(old_section_extraction, content, re.DOTALL):
        content = re.sub(old_section_extraction, new_section_extraction, content, flags=re.DOTALL)
        fixes_applied += 1
        print("✅ Fixed page section extraction method")
    
    # Apply fix 5
    if re.search(old_safety_extraction, content):
        content = re.sub(old_safety_extraction, new_safety_extraction, content)
        fixes_applied += 1
        print("✅ Fixed safety warning extraction method")
    
    if fixes_applied > 0:
        # Backup original file
        backup_path = service_path.with_suffix('.py.backup')
        with open(backup_path, 'w') as f:
            with open(service_path, 'r') as orig:
                f.write(orig.read())
        print(f"📁 Backup created: {backup_path}")
        
        # Write fixed content
        with open(service_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Applied {fixes_applied} fixes to multimodal citation service")
        return True
    else:
        print("ℹ️ No fixes needed - file appears to already be updated")
        return False

def add_improved_error_handling():
    """Add better error handling and fallback mechanisms"""
    
    service_path = Path("backend/services/multimodal_citation_service.py")
    
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Add helper method for safe pixmap conversion
    helper_method = '''
    def _safe_pixmap_to_png(self, pix) -> Optional[bytes]:
        """
        Safely convert pixmap to PNG with proper colorspace handling
        """
        try:
            if pix is None:
                return None
                
            # Check colorspace and convert appropriately
            if pix.n <= 4:  # RGB, RGBA, Grayscale
                return pix.tobytes("png")
            else:  # CMYK or other colorspaces
                try:
                    # Convert to RGB colorspace
                    pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                    png_data = pix_rgb.tobytes("png")
                    pix_rgb = None
                    return png_data
                except Exception as conversion_error:
                    logger.warning(f"RGB conversion failed: {conversion_error}")
                    # Try JPEG as fallback (handles CMYK better)
                    try:
                        return pix.tobytes("jpeg")
                    except Exception as jpeg_error:
                        logger.error(f"JPEG fallback failed: {jpeg_error}")
                        return None
                        
        except Exception as e:
            logger.error(f"Pixmap conversion failed: {e}")
            return None
        finally:
            if pix:
                pix = None  # Ensure cleanup
'''
    
    # Insert helper method after the __init__ method
    init_pattern = r'(def __init__\(self.*?\n.*?\n)'
    if re.search(init_pattern, content, re.DOTALL):
        content = re.sub(init_pattern, r'\\1' + helper_method, content, flags=re.DOTALL)
        
        with open(service_path, 'w') as f:
            f.write(content)
        
        print("✅ Added safe pixmap conversion helper method")
        return True
    
    return False

def main():
    """Run all fixes for multimodal image processing"""
    print("🔧 FIXING MULTIMODAL IMAGE PROCESSING ISSUES")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend/services/multimodal_citation_service.py").exists():
        print("❌ Error: Run this script from the project root directory")
        return
    
    # Apply fixes
    fixed_extraction = fix_image_extraction_methods()
    added_helper = add_improved_error_handling()
    
    if fixed_extraction or added_helper:
        print()
        print("✅ FIXES APPLIED SUCCESSFULLY")
        print("🔄 Restart the backend server to apply changes:")
        print("   pkill -f 'python.*main.py'")
        print("   source .venv/bin/activate && python backend/main.py")
        print()
        print("📊 Test visual citations with:")
        print("   Message: 'What temperature for Taylor C602?'")
        print("   Expected: Visual citations should now appear")
    else:
        print("ℹ️ No changes needed")

if __name__ == "__main__":
    main()