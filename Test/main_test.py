import Test.rag_old as r
import os
import dotenv

dotenv.load_dotenv()


rag_object = r.RAG(os.getenv("CLAUDE_KEY"))

prompt = rag_object.generate_response(
                    rag_object.final_wrapper_prompt("Chronic back pain is a persistent pain that can last for weeks to years. Causes can vary from muscle strain, structural issues, or nerve compression. Managing chronic back pain includes a combination of lifestyle adjustments, physical therapy, and sometimes medications. Commonly recommended medications include NSAIDs (non-steroidal anti-inflammatory drugs) and, in more severe cases, low-dose antidepressants or anticonvulsants which help modulate nerve pain. Regular low-impact exercises, such as swimming or walking, can improve muscle strength and reduce pain. Red flags indicating serious conditions include numbness, weakness in limbs, or loss of bladder control, warranting immediate medical attention.",
                   "What kind of exercises would you recommend for chronic back pain that won’t strain my muscles too much?",
                   """
User: I've been dealing with back pain for a few months now, and sometimes it gets worse when I'm sitting for long periods. My doctor mentioned that strengthening my back might help, but I don’t know where to start.
Assistant: It’s good that you're looking to strengthen your back. Many people find relief through low-impact exercises that don’t strain the back too much. I can provide some specific suggestions if you’d like.
User: That would be helpful, but I want to make sure these exercises won’t make my pain worse.
"""))

print(prompt)