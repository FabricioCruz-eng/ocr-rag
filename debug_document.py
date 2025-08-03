"""
Debug script to test Document model
"""
from models.document import Document, DocumentStatus, FileType

# Test creating a Document
try:
    doc = Document(
        filename="test.pdf",
        file_type=FileType.PDF,
        file_size=1024,
        status=DocumentStatus.UPLOADED
    )
    
    print("✅ Document created successfully")
    print(f"ID: {doc.id}")
    print(f"Vector IDs: {doc.vector_ids}")
    
    # Test serialization
    doc_dict = doc.model_dump()
    print("✅ Serialization successful")
    
    # Test deserialization
    doc2 = Document(**doc_dict)
    print("✅ Deserialization successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()