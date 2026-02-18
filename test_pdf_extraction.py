"""
Test script for PDF text extraction and chunking functionality
"""
import sys
from app import create_app
from app.ai_utils import extract_pdf_text, chunk_text, generate_embedding
import json

def test_pdf_processing(pdf_path):
    """Test PDF extraction, chunking, and embedding generation"""
    
    print(f"\n{'='*60}")
    print(f"Testing PDF: {pdf_path}")
    print(f"{'='*60}\n")
    
    # Create app context
    app = create_app()
    with app.app_context():
        # Step 1: Extract text
        print("Step 1: Extracting text from PDF...")
        text_by_page = extract_pdf_text(pdf_path)
        
        if not text_by_page:
            print("❌ No text extracted. PDF may be corrupted or scanned.")
            return
        
        print(f"✅ Extracted text from {len(text_by_page)} pages")
        print("\nSample from first page:")
        print("-" * 60)
        first_page_text = text_by_page[0]['text'][:300]
        print(f"{first_page_text}...")
        print("-" * 60)
        
        # Step 2: Chunk text
        print("\nStep 2: Chunking text...")
        chunks = chunk_text(text_by_page, chunk_size=500, overlap=100)
        
        print(f"✅ Created {len(chunks)} chunks")
        print("\nChunk statistics:")
        token_counts = [c['token_count'] for c in chunks]
        print(f"  - Average tokens per chunk: {sum(token_counts) / len(token_counts):.1f}")
        print(f"  - Min tokens: {min(token_counts)}")
        print(f"  - Max tokens: {max(token_counts)}")
        
        print("\nFirst 3 chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n  Chunk {i} (Page {chunk['page_number']}, {chunk['token_count']} tokens):")
            print(f"  {chunk['chunk_text'][:150]}...")
        
        # Step 3: Test embedding generation (only first chunk)
        print("\nStep 3: Testing embedding generation (first chunk only)...")
        try:
            embedding = generate_embedding(chunks[0]['chunk_text'])
            print(f"✅ Generated embedding: {len(embedding)} dimensions")
            print(f"  Sample values: {embedding[:5]}...")
            
            # Verify it can be serialized as JSON
            json_embedding = json.dumps(embedding)
            print(f"✅ Embedding serializes to JSON ({len(json_embedding)} characters)")
            
        except Exception as e:
            print(f"❌ Embedding generation failed: {str(e)}")
            print("   Make sure OPENAI_API_KEY is configured correctly")
        
        print(f"\n{'='*60}")
        print("Test complete!")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_extraction.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_pdf_extraction.py instance/uploads/1/1/sample.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_pdf_processing(pdf_path)
