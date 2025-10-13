"""
Test script for document-enhanced queries using VILA VLM.

Tests the /api/query/with-documents endpoint with:
- PDF files
- Images (PNG/JPG)  
- DOCX files (if available)

Shows how to combine document content with queries for:
- KB-only searches
- Deep research
- Smart routing
"""

import requests
import os
from pathlib import Path


BASE_URL = "http://localhost:8080"
TEST_DOCS_DIR = "test_docs"


def test_pdf_with_kb():
    """Test PDF parsing with KB-only query"""
    print("\n" + "="*60)
    print("Test 1: PDF + Query (KB only)")
    print("="*60)
    
    pdf_path = os.path.join(TEST_DOCS_DIR, "2510.04871v1.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"✗ PDF file not found: {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        files = {'files': ('research_paper.pdf', f, 'application/pdf')}
        data = {
            'query': 'What is this paper about? Summarize the key contributions.',
            'override': 'force:kb',
            'depth': 'deep'
        }
        
        print(f"\n📄 Uploading PDF ({os.path.getsize(pdf_path) // 1024} KB)...")
        print("⏳ Processing with VILA VLM (this may take a moment)...\n")
        
        response = requests.post(
            f"{BASE_URL}/api/query/with-documents",
            files=files,
            data=data,
            timeout=300
        )
    
    if response.ok:
        result = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Route: {result['route_taken']}")
        print(f"\n📝 Answer (first 500 chars):")
        print(result['answer'][:500] + "...")
        print(f"\n📚 Sources: {len(result['sources'])}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:500])


def test_image_with_research():
    """Test image parsing with deep research"""
    print("\n" + "="*60)
    print("Test 2: Image + Query (With Research)")
    print("="*60)
    
    # Find any image in test_docs
    image_files = list(Path(TEST_DOCS_DIR).glob("*.png")) + list(Path(TEST_DOCS_DIR).glob("*.jpg"))
    
    if not image_files:
        print(f"✗ No images found in {TEST_DOCS_DIR}")
        return
    
    img_path = str(image_files[0])
    
    with open(img_path, 'rb') as f:
        files = {'files': (os.path.basename(img_path), f, 'image/png')}
        data = {
            'query': 'Explain what this image shows and provide additional context through research.',
            'override': 'force:research',
            'depth': 'deep'
        }
        
        print(f"\n🖼️  Uploading image ({os.path.getsize(img_path) // 1024} KB)...")
        print("⏳ Processing with VILA + GPT Researcher...\n")
        
        response = requests.post(
            f"{BASE_URL}/api/query/with-documents",
            files=files,
            data=data,
            timeout=300
        )
    
    if response.ok:
        result = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Route: {result['route_taken']}")
        print(f"✓ Research: {result['research_conducted']}")
        print(f"\n📝 Answer (first 500 chars):")
        print(result['answer'][:500] + "...")
        print(f"\n📚 Sources: {len(result['sources'])}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:500])


def test_multiple_files_smart_routing():
    """Test multiple files with smart routing"""
    print("\n" + "="*60)
    print("Test 3: Multiple Files (Smart Routing)")
    print("="*60)
    
    # Collect available files
    pdf_files = list(Path(TEST_DOCS_DIR).glob("*.pdf"))
    img_files = list(Path(TEST_DOCS_DIR).glob("*.png")) + list(Path(TEST_DOCS_DIR).glob("*.jpg"))
    
    files_to_upload = []
    
    if pdf_files:
        files_to_upload.append(('files', (os.path.basename(pdf_files[0]), open(pdf_files[0], 'rb'), 'application/pdf')))
    
    if img_files:
        files_to_upload.append(('files', (os.path.basename(img_files[0]), open(img_files[0], 'rb'), 'image/png')))
    
    if not files_to_upload:
        print("✗ No test files found")
        return
    
    data = {
        'query': 'Compare and analyze the information in these documents',
        # No override - let the system decide
        'depth': 'deep'
    }
    
    print(f"\n📄🖼️  Uploading {len(files_to_upload)} file(s)...")
    print("⏳ Processing with smart routing...\n")
    
    response = requests.post(
        f"{BASE_URL}/api/query/with-documents",
        files=files_to_upload,
        data=data,
        timeout=300
    )
    
    # Close file handles
    for _, file_tuple in files_to_upload:
        if len(file_tuple) > 1 and hasattr(file_tuple[1], 'close'):
            file_tuple[1].close()
    
    if response.ok:
        result = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Route: {result['route_taken']}")
        print(f"✓ Research: {result['research_conducted']}")
        print(f"\n📝 Answer (first 500 chars):")
        print(result['answer'][:500] + "...")
        print(f"\n📚 Total sources: {len(result['sources'])}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:500])


def test_document_with_kb():
    """Test with document and query using KB"""
    print("\n" + "="*60)
    print("Test 4: Document + Query (KB Search)")
    print("="*60)
    
    pdf_files = list(Path(TEST_DOCS_DIR).glob("*.pdf"))
    
    if not pdf_files:
        print("✗ No PDF files found")
        return
    
    pdf_path = str(pdf_files[0])
    
    with open(pdf_path, 'rb') as f:
        files = {'files': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {
            'query': 'Summarize the key findings in this paper',
            'override': 'force:kb'
        }
        
        print(f"\n📄 Uploading PDF with query...")
        print("⏳ Processing with KB search...\n")
        
        response = requests.post(
            f"{BASE_URL}/api/query/with-documents",
            files=files,
            data=data,
            timeout=300
        )
    
    if response.ok:
        result = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Route: {result['route_taken']}")
        print(f"\n📝 Answer (first 500 chars):")
        print(result['answer'][:500] + "...")
        print(f"\n📚 Sources: {len(result['sources'])}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:500])


def main():
    print("\n" + "="*60)
    print("Document-Enhanced Query Testing with VILA VLM")
    print("="*60)
    
    # Check health first
    try:
        health = requests.get(f"{BASE_URL}/api/query/health", timeout=5)
        if health.ok:
            print("\n✓ System healthy!")
        else:
            print(f"\n⚠ System health check failed: {health.status_code}")
            return
    except Exception as e:
        print(f"\n✗ Cannot connect to server: {e}")
        print("Make sure the server is running on http://localhost:8080")
        return
    
    # Check test files exist
    if not os.path.exists(TEST_DOCS_DIR):
        print(f"\n⚠ {TEST_DOCS_DIR}/ directory not found")
        return
    
    pdf_count = len(list(Path(TEST_DOCS_DIR).glob("*.pdf")))
    img_count = len(list(Path(TEST_DOCS_DIR).glob("*.png"))) + len(list(Path(TEST_DOCS_DIR).glob("*.jpg")))
    
    print(f"\n📁 Test files available:")
    print(f"   📄 PDFs: {pdf_count}")
    print(f"   🖼️  Images: {img_count}")
    
    if pdf_count == 0 and img_count == 0:
        print("\n⚠ No test files found. Add PDFs or images to test_docs/")
        return
    
    # Run tests
    tests = [
        ("PDF with KB", test_pdf_with_kb),
        ("Image with Research", test_image_with_research),
        ("Multiple Files", test_multiple_files_smart_routing),
        ("Document + KB", test_document_with_kb)
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n✗ {test_name} failed: {e}")
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    print("\nSupported Formats:")
    print("  📄 PDF - converted to images, processed with VILA")
    print("  📝 DOCX - converted to PDF first, then processed")
    print("  🖼️  PNG/JPG - direct VILA processing")
    print("\nHow It Works:")
    print("  1. KB Search: Uses your query ONLY")
    print("  2. Research: Uses your query ONLY")  
    print("  3. Answer: LLM gets query + KB/research + parsed docs as context")
    print("\nQuery Modes:")
    print("  🔍 force:kb - KB search only")
    print("  🔬 force:research - Deep research with GPT Researcher")
    print("  🎯 Smart routing - System decides based on KB quality")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
