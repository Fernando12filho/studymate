"""
Test script for verifying ResourceChunk model and Resource summary fields.

This script tests:
1. Model creation without errors
2. Database migrations run successfully
3. Relationships work correctly between Resource and ResourceChunk
"""

from app import create_app
from app.extensions import db
from app.models import User, Topic, Resource, ResourceChunk
from datetime import datetime
import json

def test_models():
    """Test the new RAG-related models"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Testing RAG Models")
        print("=" * 60)
        
        # Test 1: Model definitions
        print("\n1. Testing model definitions...")
        try:
            # Check ResourceChunk model attributes
            assert hasattr(ResourceChunk, 'id'), "ResourceChunk missing 'id'"
            assert hasattr(ResourceChunk, 'resource_id'), "ResourceChunk missing 'resource_id'"
            assert hasattr(ResourceChunk, 'chunk_text'), "ResourceChunk missing 'chunk_text'"
            assert hasattr(ResourceChunk, 'chunk_index'), "ResourceChunk missing 'chunk_index'"
            assert hasattr(ResourceChunk, 'page_number'), "ResourceChunk missing 'page_number'"
            assert hasattr(ResourceChunk, 'embedding'), "ResourceChunk missing 'embedding'"
            assert hasattr(ResourceChunk, 'token_count'), "ResourceChunk missing 'token_count'"
            assert hasattr(ResourceChunk, 'created_at'), "ResourceChunk missing 'created_at'"
            
            # Check Resource model has new summary fields
            assert hasattr(Resource, 'summary'), "Resource missing 'summary'"
            assert hasattr(Resource, 'summary_generated_at'), "Resource missing 'summary_generated_at'"
            
            print("✓ All model attributes defined correctly")
        except AssertionError as e:
            print(f"✗ Model definition error: {e}")
            return False
        
        # Test 2: Create tables
        print("\n2. Testing table creation...")
        try:
            db.create_all()
            print("✓ Tables created successfully")
        except Exception as e:
            print(f"✗ Table creation error: {e}")
            return False
        
        # Test 3: Create test data
        print("\n3. Testing data creation and relationships...")
        try:
            # Create a test user
            test_user = User.query.first()
            if not test_user:
                test_user = User(
                    username="test_user",
                    email="test@example.com",
                    password="test_password"
                )
                db.session.add(test_user)
                db.session.flush()
            
            # Create a test topic
            test_topic = Topic.query.first()
            if not test_topic:
                test_topic = Topic(
                    name="Test Topic",
                    description="Test topic for RAG",
                    user_id=test_user.id
                )
                db.session.add(test_topic)
                db.session.flush()
            
            # Create a test resource with summary
            test_resource = Resource(
                title="Test PDF Document",
                resource_type="pdf",
                file_path="/test/path.pdf",
                summary="This is a test summary of the document.",
                summary_generated_at=datetime.utcnow(),
                user_id=test_user.id,
                topic_id=test_topic.id
            )
            db.session.add(test_resource)
            db.session.flush()
            
            print(f"✓ Created test resource (ID: {test_resource.id})")
            
            # Create test chunks
            test_chunks = []
            for i in range(3):
                # Create a sample embedding (normally would be from OpenAI)
                sample_embedding = [0.1 * j for j in range(1536)]  # OpenAI embeddings are 1536-dimensional
                
                chunk = ResourceChunk(
                    resource_id=test_resource.id,
                    chunk_text=f"This is test chunk {i+1} of the document.",
                    chunk_index=i,
                    page_number=i + 1,
                    embedding=json.dumps(sample_embedding),
                    token_count=10 + i * 5
                )
                db.session.add(chunk)
                test_chunks.append(chunk)
            
            db.session.commit()
            print(f"✓ Created {len(test_chunks)} test chunks")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Data creation error: {e}")
            return False
        
        # Test 4: Test relationships
        print("\n4. Testing relationships...")
        try:
            # Reload the resource
            resource = Resource.query.filter_by(title="Test PDF Document").first()
            assert resource is not None, "Could not find test resource"
            
            # Test the chunks relationship
            chunks = resource.chunks
            assert len(chunks) > 0, "Resource has no chunks"
            print(f"✓ Resource has {len(chunks)} chunks")
            
            # Test accessing chunk data
            first_chunk = chunks[0]
            assert first_chunk.chunk_text.startswith("This is test chunk"), "Chunk text incorrect"
            assert first_chunk.resource_id == resource.id, "Chunk resource_id mismatch"
            print("✓ Chunk data accessible and correct")
            
            # Test summary fields
            assert resource.summary is not None, "Resource summary is None"
            assert resource.summary_generated_at is not None, "Resource summary_generated_at is None"
            print("✓ Summary fields working correctly")
            
            # Test embedding deserialization
            embedding = json.loads(first_chunk.embedding)
            assert isinstance(embedding, list), "Embedding is not a list"
            assert len(embedding) == 1536, f"Embedding length is {len(embedding)}, expected 1536"
            print("✓ Embedding serialization/deserialization working")
            
        except Exception as e:
            print(f"✗ Relationship test error: {e}")
            return False
        
        # Test 5: Query tests
        print("\n5. Testing queries...")
        try:
            # Query chunks by resource
            chunks_by_resource = ResourceChunk.query.filter_by(resource_id=resource.id).all()
            assert len(chunks_by_resource) == 3, f"Expected 3 chunks, found {len(chunks_by_resource)}"
            print(f"✓ Query by resource_id works: found {len(chunks_by_resource)} chunks")
            
            # Query chunks ordered by index
            ordered_chunks = ResourceChunk.query.filter_by(
                resource_id=resource.id
            ).order_by(ResourceChunk.chunk_index).all()
            
            assert ordered_chunks[0].chunk_index == 0, "Chunks not ordered correctly"
            print("✓ Ordering by chunk_index works")
            
            # Query resources with summaries
            resources_with_summaries = Resource.query.filter(
                Resource.summary.isnot(None)
            ).all()
            assert len(resources_with_summaries) > 0, "No resources with summaries found"
            print(f"✓ Query for resources with summaries works: found {len(resources_with_summaries)}")
            
        except Exception as e:
            print(f"✗ Query test error: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print("\nModel Summary:")
        print(f"  - ResourceChunk table: ✓")
        print(f"  - Resource.summary field: ✓")
        print(f"  - Resource.summary_generated_at field: ✓")
        print(f"  - Resource -> ResourceChunk relationship: ✓")
        print(f"  - Embedding storage (JSON): ✓")
        
        return True

if __name__ == "__main__":
    success = test_models()
    
    if success:
        print("\n✓ RAG models are ready for use!")
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
