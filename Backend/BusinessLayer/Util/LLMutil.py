import json
import re
from typing import List

import requests


class LLMutil:
    """Utility wrapper around a Hugging Face Inference API endpoint that extracts
    the most relevant course topics for a given exam question.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMutil, cls).__new__(cls)
            cls._instance._initialized = False  # נעשה איניט רק פעם אחת
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.token= "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"  # Hugging Face token for authentication
        self.model_api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

    # # NOTE: kept the original method name so existing call‑sites remain intact
    # def find_question_topics_by_text_cloud(self, question_text, course_topics ) :
    #     """Return the subset of *course_topics* that the LLM deems relevant.
    #
    #     Parameters
    #     ----------
    #     question_text : str
    #         The raw text of the exam question.
    #     course_topics : list[str]
    #         All possible topics for the course – will be filtered down based on the model output.
    #     max_new_tokens : int, optional
    #         Generation length cap for deterministic responses.
    #
    #     Returns
    #     -------
    #     list[str]
    #         Relevant topics or an empty list when nothing is detected / an error occurs.
    #     """
    #
    #     if not question_text or not course_topics:
    #         print("קלט טקסט שאלה ריק או רשימת נושאים ריקה. מחזיר רשימה ריקה.")
    #         return []
    #
    #     topics_formatted = "\n".join(f"- {topic}" for topic in course_topics)
    #
    #     prompt = f"""
    #     Given the following exam question:
    #     "{question_text}"
    #
    #     And the following list of potential topics:
    #     {topics_formatted}
    #
    #     Please identify only the most relevant topics from the list that directly relate to the question.
    #     Return your answer as a Python list of strings. Do not include any other text or explanation, just the list.
    #     For example: ['Topic 1', 'Topic 2']
    #
    #     Relevant topics:
    #     """
    #
    #     headers = {
    #         "Authorization": f"Bearer {self.token}",
    #         "Content-Type": "application/json",
    #     }
    #
    #     payload = {
    #         "inputs": prompt,
    #         "parameters": {
    #             "max_new_tokens": 100,
    #             "return_full_text": False,
    #             "do_sample": False,
    #         },
    #     }
    #
    #     try:
    #         response = requests.post(
    #             self.model_api_url,
    #             headers=headers,
    #             data=json.dumps(payload),
    #             timeout=30,
    #         )
    #         response.raise_for_status()
    #     except requests.exceptions.RequestException as e:
    #         print(f"שגיאת בקשת HTTP: {e}")
    #         return []
    #
    #     try:
    #         result = response.json()
    #         print(f"התגובה מה-API: {result}")
    #     except json.JSONDecodeError as e:
    #         print(f"שגיאת ניתוח JSON מהתגובה: {e}. התגובה כטקסט: {response.text}")
    #         return []
    #
    #     # --- extract generated text -------------------------------------------------
    #     if isinstance(result, list) and result and "generated_text" in result[0]:
    #         output_text = result[0]["generated_text"].strip()
    #     elif isinstance(result, dict) and "generated_text" in result:
    #         output_text = result["generated_text"].strip()
    #     else:
    #         print("שגיאה: מבנה תגובה לא צפוי מה‑API.")
    #         return []
    #
    #     # Strategy 1: Python‑style list inside square brackets
    #     bracket_match = re.search(r"\[.*?\]", output_text, flags=re.S)
    #     if bracket_match:
    #         list_str = bracket_match.group(0)
    #         try:
    #             extracted = json.loads(list_str.replace("'", '"'))
    #             if isinstance(extracted, list):
    #                 return [t for t in extracted if t in course_topics]
    #         except Exception:
    #             pass  # fall through to strategy 2
    #
    #     # Strategy 2: Bullet‑list style (lines that start with "- ")
    #     bullet_matches = re.findall(r"-\s+(.*)", output_text)
    #     if bullet_matches:
    #         extracted = [m.strip() for m in bullet_matches]
    #         print("נושאים מחולצים:", extracted)
    #         topics = [t for t in extracted if t in course_topics]
    #         print("נושאים רלוונטיים:", topics)
    #         return topics
    #
    #     print("שגיאה: לא נמצאה רשימה תקינה בפלט המודל.")
    #     print(f"פלט המודל המלא: {output_text}")
    #     return []

#     def extract_topics_from_syllabus_text(self, syllabus_text: str) -> list[str]:
#         print("מתחיל לחלץ נושאים מטקסט הסילבוס...", syllabus_text)
#         if not syllabus_text:
#             print("שגיאה: טקסט סילבוס ריק.")
#             return []
#         prompt = f"""
#     You are a helpful assistant. Given the following syllabus text:
#
#     \"\"\"{syllabus_text}\"\"\"
#
#     Extract a clean list of course topics (without explanations, numbering, or formatting).
# ⚠️ Only return a valid Python list of strings.
# ⚠️ Do not return numbered topics or any extra text.
#
# Example:
# ['Probability basics', 'Bayes law', 'Discrete random variables']
#
# Topics:
# """
#
#         headers = {
#             "Authorization": f"Bearer {self.token}",
#             "Content-Type": "application/json"
#         }
#
#         payload = {
#             "inputs": prompt,
#             "parameters": {
#                 "max_new_tokens": 200,
#                 "return_full_text": False,
#                 "do_sample": False
#             }
#         }
#
#         try:
#             response = requests.post(self.model_api_url, headers=headers, data=json.dumps(payload))
#             response.raise_for_status()
#             result = response.json()
#
#             print(f"התגובה מה-API: {result}")
#
#             output_text = ''
#             if isinstance(result, list) and result and 'generated_text' in result[0]:
#                 output_text = result[0]['generated_text'].strip()
#             elif isinstance(result, dict) and 'generated_text' in result:
#                 output_text = result['generated_text'].strip()
#             else:
#                 print("שגיאה: מבנה תגובה לא צפוי מה-API.")
#                 return []
#
#             # נסה לפרסר כפייתון ליסט
#             match = re.search(r"\[.*?\]", output_text, re.DOTALL)
#             if match:
#                 list_str = match.group(0)
#                 try:
#                     extracted_list = eval(list_str)
#                     if isinstance(extracted_list, list) and all(isinstance(item, str) for item in extracted_list):
#                         return [item.strip() for item in extracted_list]
#                 except Exception as e:
#                     print(f"שגיאה ב-eval: {e}")
#                     print(f"טקסט הפלט: {list_str}")
#
#             # נסה לפרסר שורות ממוספרות
#             numbered_lines = re.findall(r'\d+\.\s+(.*)', output_text)
#             if numbered_lines:
#                 return [line.strip() for line in numbered_lines]
#
#             # נסה לפרסר bullet points
#             bullet_matches = re.findall(r"-\s+(.*)", output_text)
#             if bullet_matches:
#                 return [m.strip() for m in bullet_matches]
#
#             print("שגיאה: לא הצליח לפרסר את הפלט.")
#             return []
#
#         except requests.exceptions.RequestException as e:
#             print(f"שגיאת HTTP: {e}")
#             return []
#         except Exception as e:
#             print(f"שגיאה כללית: {e}")
#             return []

    def extract_topics_from_syllabus_text(self , syllabus_text: str, course_name: str) -> str:
        prompt = f"""
                You are a helpful assistant. Given the following syllabus text:
                course name is : {course_name} .
                \"\"\"{syllabus_text}\"\"\"

                Extract a clean list of course topics (without explanations, numbering, or formatting).
                you may include topics that are not explicitly mentioned in the syllabus, but are relevant to the course.
            ⚠️ Only return a valid Python list of strings.
            ⚠️ Do not return numbered topics or any extra text.
            ⚠️ Do not include course name in any topic.


            Example:
            ['Probability basics', 'Bayes law', 'Discrete random variables']

            Topics:
            """

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",
                "prompt": prompt,
                "stream": False
            }
        )
        print("response: ", response.json())
        if response.status_code != 200:
            print(f"שגיאה: בקשת ה-API נכשלה עם סטטוס {response.status_code}")
            return []

        try:

            response.raise_for_status()
            result = response.json()

            print(f"התגובה מה-API: {result}")

            output_text = ''
            if isinstance(result, dict) and 'response' in result:
                output_text = result['response'].strip()
            elif isinstance(result, list) and result and 'generated_text' in result[0]:
                output_text = result[0]['generated_text'].strip()
            elif isinstance(result, dict) and 'generated_text' in result:
                output_text = result['generated_text'].strip()
            else:
                print("שגיאה: מבנה תגובה לא צפוי מה-API.")
                return []

            # נסה לפרסר כפייתון ליסט
            match = re.search(r"\[.*?\]", output_text, re.DOTALL)
            if match:
                list_str = match.group(0)
                try:
                    extracted_list = eval(list_str)
                    if isinstance(extracted_list, list) and all(isinstance(item, str) for item in extracted_list):
                        return list(set([item.strip() for item in extracted_list]))
                except Exception as e:
                    print(f"שגיאה ב-eval: {e}")
                    print(f"טקסט הפלט: {list_str}")

            # נסה לפרסר שורות ממוספרות
            numbered_lines = re.findall(r'\d+\.\s+(.*)', output_text)
            if numbered_lines:
                return list(set([line.strip() for line in numbered_lines]))

            # נסה לפרסר bullet points
            bullet_matches = re.findall(r"-\s+(.*)", output_text)
            if bullet_matches:
                return list(set([m.strip() for m in bullet_matches]))

            print("שגיאה: לא הצליח לפרסר את הפלט.")
            return []

        except requests.exceptions.RequestException as e:
            print(f"שגיאת HTTP: {e}")
            return []
        except Exception as e:
            print(f"שגיאה כללית: {e}")
            return []

    def find_question_topics_by_text_cloud(self, question_text, course_topics):
        """Return the subset of *course_topics* that the LLM deems relevant (using Ollama).

        Parameters
        ----------
        question_text : str
            The raw text of the exam question.
        course_topics : list[str]
            All possible topics for the course – will be filtered down based on the model output.

        Returns
        -------
        list[str]
            Relevant topics or an empty list when nothing is detected / an error occurs.
        """

        if not question_text or not course_topics:
            print("קלט טקסט שאלה ריק או רשימת נושאים ריקה. מחזיר רשימה ריקה.")
            return []

        topics_formatted = "\n".join(f"- {topic}" for topic in course_topics)

        prompt = f"""
        Given the following exam question:
        "{question_text}"

        And the following list of potential topics:
        {topics_formatted}

        Please identify only the most relevant topics from the list that directly relate to the question.
        Return your answer as a Python list of strings. Do not include any other text or explanation, just the list.
        For example: ['Topic 1', 'Topic 2']

        Relevant topics:
        """

        payload = {
            "model": "gemma3:1b",  # או כל מודל קטן אחר שהתקנת ב-Ollama
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"שגיאת HTTP: {e}")
            return []

        try:
            result = response.json()
            output_text = result.get("response", "").strip()
            print(f"הפלט מהמודל: {output_text}")
        except Exception as e:
            print(f"שגיאת עיבוד תגובה: {e}")
            return []

        # Strategy 1: Extract from Python-style list
        match = re.search(r"\[.*?\]", output_text, re.DOTALL)
        if match:
            list_str = match.group(0)
            try:
                parsed = eval(list_str)
                if isinstance(parsed, list):
                    return [t for t in parsed if t in course_topics]
            except Exception as e:
                print(f"שגיאה ב-eval: {e}")
                print(f"טקסט הפלט: {list_str}")

        # Strategy 2: Bullet points
        bullets = re.findall(r"-\s+(.*)", output_text)
        if bullets:
            return list(set([b.strip() for b in bullets if b.strip() in course_topics]))

        print("שגיאה: לא הצליח לפרסר את הפלט.")
        print(f"פלט המודל המלא: {output_text}")
        return []




