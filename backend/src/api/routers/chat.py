from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Iterator
import traceback
import re
import json

from src.schemas import ChatRequest, ChatResponse
from src.util.io import message, save_chat_log
from src.llm.client import get_openai_client
from src.core.config import SYSTEM_PROMPT, MODEL_CHAT
from src.rag.retriever import retrieve, build_context_block

router = APIRouter()


def _get_client():
    """Get OpenAI client with error handling."""
    try:
        return get_openai_client()
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI client initialization failed: {str(e)}",
        )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        # Get client
        client = _get_client()

        # ----- RAG retrieval with error handling -----
        try:
            retrieved = retrieve(req.resume_text or "", req.message or "")
            context_block = build_context_block(
                req.resume_text or "",
                req.message or "",
                retrieved,
            )
        except Exception as e:
            print(f"[RAG] Error during retrieval: {e}")
            print(traceback.format_exc())
            # Continue with empty context if retrieval fails
            retrieved = []
            context_block = build_context_block(
                req.resume_text or "",
                req.message or "",
                [],
            )

        # ----- Build messages (no memory augmentation) -----
        messages = [message("system", SYSTEM_PROMPT)]
        if req.resume_text:
            messages.append(
                message(
                    "user",
                    f"(Resume context)\n{(req.resume_text or '')[:4000]}",
                )
            )
        messages.append(message("user", context_block))

        # ----- OpenAI API call with error handling -----
        try:
            comp = client.chat.completions.create(
                model=MODEL_CHAT,
                temperature=0.2,
                messages=messages,
            )
            reply = comp.choices[0].message.content or ""
        except Exception as e:
            print(f"[OpenAI] Error during completion: {e}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(e)}",
            )

        # ----- Save chat log (non-critical, don't fail if this errors) -----
        try:
            save_chat_log(req.message, reply)
        except Exception as e:
            print(f"[Log] Error saving chat log: {e}")

        # ----- Handle study plan update markers -----
        citations: list[str] = []

        # Ensure reply is not empty
        if not reply or not reply.strip():
            reply = (
                "I apologize, but I couldn't generate a response. "
                "Please try again or rephrase your question."
            )

        study_plan_update = None
        reply_text = reply

        # Look for [STUDY_PLAN_UPDATE:...] pattern
        update_pattern = r"\[STUDY_PLAN_UPDATE:([^\]]+)\]"
        match = re.search(update_pattern, reply)

        if match:
            try:
                # Parse the update parameters
                params_str = match.group(1)
                # Extract user_id, action, and params
                user_id_match = re.search(r"user_id=([^,]+)", params_str)
                action_match = re.search(r"action=([^,]+)", params_str)
                params_match = re.search(r"params=({.+?})", params_str)

                if action_match:
                    study_plan_update = {
                        "user_id": (
                            user_id_match.group(1).strip()
                            if user_id_match
                            else "current_user"
                        ),
                        "action": action_match.group(1).strip(),
                        "params": (
                            json.loads(params_match.group(1)) if params_match else {}
                        ),
                    }
                    # Remove the action marker from the reply
                    reply_text = re.sub(update_pattern, "", reply).strip()
            except Exception as e:
                print(f"[Chat] Error parsing study plan update: {e}")

        # Add study plan update info to citations if present
        if study_plan_update:
            citations.append(f"STUDY_PLAN_UPDATE:{json.dumps(study_plan_update)}")

        return ChatResponse(reply=reply_text, citations=citations)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chat] Unexpected error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


# Optional: SSE streaming endpoint
@router.get("/chat/stream")
def chat_stream(message: str, resume_text: str = "", user_id: str | None = None):
    # Validate input
    if not message or not message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    # local helper to avoid shadowing outer "message"
    def message_fn(role, content):
        return {"role": role, "content": content}

    def gen() -> Iterator[bytes]:
        try:
            client = _get_client()

            # ----- RAG retrieval with error handling -----
            try:
                retrieved = retrieve(resume_text or "", message or "")
                context_block = build_context_block(
                    resume_text or "", message or "", retrieved
                )
            except Exception as e:
                print(f"[RAG] Error during retrieval: {e}")
                print(traceback.format_exc())
                retrieved = []
                context_block = build_context_block(
                    resume_text or "", message or "", []
                )

            # ----- Build messages (no memory augmentation) -----
            messages = [message_fn("system", SYSTEM_PROMPT)]
            if resume_text:
                messages.append(
                    message_fn(
                        "user",
                        f"(Resume context)\n{(resume_text or '')[:4000]}",
                    )
                )
            messages.append(message_fn("user", context_block))

            # ----- Stream response -----
            stream = client.chat.completions.create(
                model=MODEL_CHAT,
                temperature=0.2,
                messages=messages,
                stream=True,
            )

            partial = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    partial += delta
                    yield f"data: {delta}\n\n".encode("utf-8")

            # ----- Save chat log (non-critical) -----
            try:
                save_chat_log(message, partial)
            except Exception as e:
                print(f"[Log] Error saving chat log (stream): {e}")

        except Exception as e:
            print(f"[Stream] Error: {e}")
            print(traceback.format_exc())
            error_msg = f"Error: {str(e)}"
            yield f"data: {error_msg}\n\n".encode("utf-8")

    return StreamingResponse(gen(), media_type="text/event-stream")

