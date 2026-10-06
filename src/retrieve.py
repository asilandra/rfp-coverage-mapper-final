"""
retrieve.py - STAGE 3 of the tool: rank the slides by how relevant they are to
each requirement, using a local embedding model (free, runs on CPU, no API).

An embedding model turns a piece of text into a list of numbers (a "vector")
that captures its MEANING. Texts with similar meaning get similar vectors, even
when they use different words ("pilots" vs "rapid prototypes"). We compare the
requirement's vector with each slide's vector (cosine similarity, 0 to 1).

How the ranking is used (decision based on a measurement on Day 4):
  - deck of up to MAX_SLIDES_FOR_JUDGE slides -> the judge sees ALL slides,
    most relevant first (retrieval orders them, it never hides any)
  - bigger deck -> the judge sees only the MAX_SLIDES_FOR_JUDGE most relevant
On our test deck, a top-5 shortlist missed the right slide for 1 of 14
requirements, so a hard shortlist is only used when the deck is large.
"""
import numpy as np

EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
MAX_SLIDES_FOR_JUDGE = 25


class SlideRetriever:
    def __init__(self, deck, model_name=EMBEDDING_MODEL):
        self.slides = deck["slides"]
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, device="cpu")
            texts = [s["visible_text"] for s in self.slides]   # what the client sees; notes excluded
            self.vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            self.method = f"embeddings ({model_name.split('/')[-1]})"
        except Exception as e:
            # Safe fallback: without embeddings the judge still sees every slide, in deck order
            self.method = f"none: embedding model unavailable ({str(e)[:100]}); slides kept in deck order"

    def rank(self, requirement, limit=MAX_SLIDES_FOR_JUDGE):
        """Return [{'slide_number': n, 'score': s}, ...], most relevant first, at most `limit` slides."""
        if self.model is None:
            ranked = [{"slide_number": s["slide_number"], "score": None} for s in self.slides]
        else:
            query = f"{requirement['requirement']} {requirement['source_quote']}"
            q = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
            scores = self.vectors @ q          # cosine similarity (vectors are normalised)
            order = np.argsort(-scores)
            ranked = [{"slide_number": self.slides[i]["slide_number"], "score": round(float(scores[i]), 3)}
                      for i in order]
        return ranked[:limit]
