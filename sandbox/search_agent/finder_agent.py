# resume_similarity.py
import os
import docx
from pdfminer.high_level import extract_text as extract_text_pdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tools.helpful_functions import *


def compute_similarity(job_description_path, resumes_directory_path):
    """
    Computes the cosine similarity between a job description and resumes.

    Args:
        job_description_path (str): Path to the job description file.
        resumes_directory_path (str): Path to the directory containing resumes.

    Returns:
        list of tuples: Each tuple contains (resume_index, similarity_score).
    """
    texts = [read_text_file(job_description_path)]

    for filename in os.listdir(resumes_directory_path):
        file_path = os.path.join(resumes_directory_path, filename)
        extracted_text = read_text_file(file_path)
        texts.append(extracted_text)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    similarity_scores = cosine_similarities.flatten()
    ranked_resume_indices = similarity_scores.argsort()[::-1]  # From most similar to least
    ranking = [(index, similarity_scores[index]) for index in ranked_resume_indices]

    return ranking


# This block is just for testing and won't run when this file is imported elsewhere
if __name__ == '__main__':
    job_description_path = 'job_descriptions/Electrician_4_Job_Description.docx'
    resumes_directory_path = 'resumes/'
    ranking = compute_similarity(job_description_path, resumes_directory_path)
    print(ranking)
