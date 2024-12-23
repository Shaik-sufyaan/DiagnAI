import Test.rag_old as r
import dotenv
import os

dotenv.load_dotenv()
voyage_api = os.getenv("VOYAGE_API_KEY")

data = r.Data_Handler(voyage_api)

text_directory = "/Users/varunahlawat/AI_ATL_LOCAL/DataCorpus"

############ VECTOR DB ############
vector_directory = "/Users/varunahlawat/AI_ATL_LOCAL/VectorDB"

if not os.path.exists(vector_directory):
    size = 0
    print("VectorDB directory doesn't exist; creating it now...")
    vector_db = data.create_vector_db(vector_directory)
else:
    size = data.collection_size

print(size)
print(type(size))

# vector_chunks = data.document_load(text_directory)

# for i in range(size , size + len(vector_chunks)+1):
#     doc_id = f"doc_{i}"
#     data.append(vector_chunks, doc_id)

