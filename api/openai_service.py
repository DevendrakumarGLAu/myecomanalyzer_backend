from dotenv import load_dotenv
import os
import logging
from typing import Iterator

from google import genai

load_dotenv()

logger = logging.getLogger("gemini")


class LangChainService:

    MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # print("-----model name ---------", MODEL)
    # client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # response = client.models.generate_content(
    #     model=os.getenv("GEMINI_MODEL"),
    #     contents="Say hello in 1 line"
    # )

    # print(response.text)

    @classmethod
    def _client(cls):
        api_key = os.getenv("GEMINI_API_KEY")
        # client = genai.Client(api_key=api_key)

        # for m in client.models.list():
        #     print(m.name)

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        return genai.Client(api_key=api_key)

    @classmethod
    def _convert_messages(cls, messages):
        prompt = ""

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt += f"System: {content}\n"

            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

            else:
                prompt += f"User: {content}\n"

        return prompt

    @classmethod
    def create_chat_completion(cls, messages, stream=False):

        try:
            client = cls._client()

            prompt = cls._convert_messages(messages)

            if stream:
                return cls._stream_response(client, prompt)

            response = client.models.generate_content(
                model=cls.MODEL,
                contents=prompt
            )

            answer = response.text.strip()

            logger.info("Gemini response generated")

            return answer

        except Exception as exc:
            logger.exception("Gemini API failed")
            raise RuntimeError("AI service unavailable.") from exc

    @classmethod
    def _stream_response(cls, client, prompt) -> Iterator[str]:

        response = client.models.generate_content_stream(
            model=cls.MODEL,
            contents=prompt
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text


# Backward compatibility
OpenAIService = LangChainService

# from dotenv import load_dotenv
# import os

# import logging
# from typing import Iterator

# from langchain_openai import ChatOpenAI
# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# from django.conf import settings
# load_dotenv()

# logger = logging.getLogger("langchain")


# class LangChainService:
#     MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
#     TEMPERATURE = float(os.getenv("LANGCHAIN_TEMPERATURE", 0.25))
#     MAX_TOKENS = int(os.getenv("LANGCHAIN_MAX_TOKENS", 800))

#     @classmethod
#     def _get_api_key(cls) -> str:
#         # api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
#         api_key = os.getenv("GEMINI_API_KEY")

#         print(f"Using LangChain api_key: {api_key}")
        
#         if not api_key:
#             raise RuntimeError("Gemini API key is not configured. Set GEMINI_API_KEY.")
#         return api_key

#     @classmethod
#     def _get_llm(cls, streaming: bool = False):
#         return ChatOpenAI(
#             model=cls.MODEL,
#             temperature=cls.TEMPERATURE,
#             max_tokens=cls.MAX_TOKENS,
#             api_key=cls._get_api_key(),
#             streaming=streaming,
#         )

#     @classmethod
#     def _convert_messages(cls, messages: list[dict[str, str]]):
#         """Convert OpenAI message format to LangChain format"""
#         langchain_messages = []
#         for msg in messages:
#             role = msg.get("role", "user")
#             content = msg.get("content", "")
            
#             if role == "system":
#                 langchain_messages.append(SystemMessage(content=content))
#             elif role == "assistant":
#                 langchain_messages.append(AIMessage(content=content))
#             else:
#                 langchain_messages.append(HumanMessage(content=content))
        
#         return langchain_messages

#     @classmethod
#     def create_chat_completion(cls, messages: list[dict[str, str]], stream: bool = False) -> str | Iterator[str]:
#         try:
#             llm = cls._get_llm(streaming=stream)
#             langchain_messages = cls._convert_messages(messages)

#             if stream:
#                 return cls._stream_response(llm, langchain_messages)
            
#             response = llm.invoke(langchain_messages)
#             answer = response.content.strip()
#             logger.debug("LangChain completion generated successfully.")
#             return answer
        
#         except Exception as exc:
#             logger.exception("Failed to call LangChain ChatOpenAI API")
#             raise RuntimeError("AI service unavailable. Please try again later.") from exc

#     @classmethod
#     def _stream_response(cls, llm, messages) -> Iterator[str]:
#         """Stream response from LLM"""
#         for chunk in llm.stream(messages):
#             if chunk.content:
#                 yield chunk.content


# # Keep alias for backward compatibility
# OpenAIService = LangChainService


