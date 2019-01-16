import spacy

# Load English tokenizer, tagger, parser, NER and word vectors
nlp = spacy.load('en_core_web_sm')


def get_doc_entity(text):
    doc = nlp(text)
    # Find named entities, phrases and concepts
    for entity in doc.ents:
        yield str(entity.label_)
