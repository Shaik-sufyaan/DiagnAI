import rag as r
import VectorDB as v
import os
from dotenv import load_dotenv


def main(PromptIn = "", conv_history=""):
    load_dotenv()
    claude_api = os.getenv("CLAUDE_KEY")
    voyage_api = os.getenv("VOYAGE_API_KEY")

    # Pass the input prompt in the semantic search
    # Initialize embedding and vectorization
    Voyage = r.VoyageEmbedding(voyage_api)
    Medical_Context_List_Dict = Voyage.hybrid_search(PromptIn, top_k=2) # LIST of dictionaries
    Medical_Context_List = [i["text"] for i in Medical_Context_List]

    # initialize RAG:
    rag_model = r.RAG(claude_api)
    final_wrapper_prompt = rag_model.final_wrapper_prompt(context=f"[i for i in Medical_Context_List]", query=PromptIn, conversation_history=conv_history)

    Output = rag_model.generate_response(final_wrapper_prompt)
    return Output


if __name__=="__main__":
    main()
