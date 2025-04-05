import PyPDF2
import spacy
import google.generativeai as genai
import os

class PDFChatProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.pdf_text = ""
        self.entities = {}
        self.current_file = ""


        self.gemini_api_key = os.getenv("GEMINI_API_KEY") 
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not found.")
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")


        self.huggingface_models = {
            "bert": "kedarnath7/legalbert4modelworking",
            "flan-t5": "kedarnath7/T5_1modelworking",
        }

    def load_pdf(self, pdf_path: str):
        if os.path.getsize(pdf_path) > 200 * 1024 * 1024:
            raise ValueError("File size exceeds 200 MB")
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            self.pdf_text = ""
            for page in pdf_reader.pages:
                self.pdf_text += page.extract_text() or ""
        self.current_file = pdf_path
        self._extract_entities()

    def _extract_entities(self):

        doc = self.nlp(self.pdf_text)
        self.entities = {
            "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
            "people": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
            "orgs": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
            "legal": [ent.text for ent in doc.ents if ent.label_ in ["LAW", "NORP"]],
        }

    def summarize(self, size: str = "medium") -> str:
        word_limits = {"small": 50, "medium": 150, "large": 300}
        limit = word_limits.get(size, 150)
        prompt = (
            f"Below is a document. Please summarize it in approximately {limit} words. "
            f"Use only the information provided in the document. Do not add any external knowledge.\n\n"
            f"Document:\n\n{self.pdf_text[:10000]}\n\nSummary:"
        )
        response = self.gemini_model.generate_content(prompt)
        return response.text

    def compliance_check(self) -> str:
        prompt = (
            f"Review the following document for compliance issues (e.g., legal terms, sensitive data). "
            f"Use only the information provided in the document. Do not add any external knowledge.\n\n"
            f"Document:\n\n{self.pdf_text[:10000]}\n\nFindings:"
        )
        response = self.gemini_model.generate_content(prompt)
        return response.text

    def process_query(self, message: str) -> str:
        message = message.lower().strip()
        
        if "summarize" in message:
            size = "medium"
            if "small" in message:
                size = "small"
            elif "large" in message:
                size = "large"
            return self.summarize(size)
        
        elif "compliance" in message:
            return self.compliance_check()
        
        elif "date" in message:
            return f"Important dates: {', '.join(self.entities['dates'][:10])}"
        
        elif "people" in message or "person" in message:
            return f"Key people: {', '.join(self.entities['people'][:10])}"
        
        elif "legal" in message:
            return f"Legal entities: {', '.join(self.entities['legal'][:10])}"
        
        #elif "places" in message:
        #   return f"Important places: {', '.join(self.entities['places'][:10])}"
        
        else:
            prompt = (
                f"You are a helpful assistant. Your knowledge is strictly limited to the following document. "
                f"Do not use any external knowledge. If the answer is not in the document, say 'I don't know'.\n\n"
                f"Document:\n\n{self.pdf_text[:5000]}\n\n"
                f"User asks: {message}\n\nAnswer:"
            )
            response = self.gemini_model.generate_content(prompt)
            return response.text