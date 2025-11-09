#
# import os, json, pandas as pd, numpy as np
# from docx import Document
# from docx.shared import Pt
# from pathlib import Path
#
# from openai import OpenAI

# class LLmModel:
#     def __init__(self, system_prompt, temperature = 0.7, openai_model='gpt-4.0-mini', ):
#         self.openai_model = openai_model
#         self.client = OpenAI()
#         self.system_prompt = system_prompt
#         self.temperature = temperature
#
#     def llm_complete(self, user_prompt, ):
#         resp = self.client.chat.completions.create(
#             model="gpt-4.0-mini",
#             messages=[
#                 {"role": "system", "content": self.system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             temperature=self.temperature
#         )
#         return resp.choices[0].message.content
#
#     def generate_full_proposal(self, base_context: str, style_desc: str,):
#
#         system_prompt = f"""You are an expert proposal writer. You write full, professional RFP proposals that are factual and grounded in provided context.
#         Follow this structure exactly:
#         - Executive Summary
#         - Technical Approach
#         - Project Plan & Timeline
#         - Evidence & Case References
#         - Compliance & Risk
#         - Pricing Summary (high-level)
#         - Assumptions & Exclusions
#
#         Rules:
#         - Use only the provided context. If information is missing, state that explicitly.
#         - Keep placeholders like <CLIENT>, <COUNTRY>, <DURATION> intact.
#         - Keep tone/style: {style_desc}.
#         - Avoid hallucinations; no invented certifications or metrics.
#         """
#
#         user_prompt = f"""Here is the RFP context (extracted content from internal documents):
#         =================
#         {base_context}
#         =================
#
#         Write the full proposal document now.
#         """
#
#         return self.llm_complete(system_prompt, user_prompt)
#
