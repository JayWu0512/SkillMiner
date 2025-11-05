from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Iterator

from src.schemas import ChatRequest, ChatResponse
from src.util.io import message, save_chat_log
from src.llm.client import get_openai_client
from src.core.config import SYSTEM_PROMPT, MODEL_CHAT
from src.rag.retriever import retrieve, build_context_block

router = APIRouter()
client = get_openai_client()

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # RAG
    retrieved = retrieve(req.resume_text or "", req.message or "")
    context_block = build_context_block(req.resume_text or "", req.message or "", retrieved)

    # Build messages
    messages = [
        message("system", SYSTEM_PROMPT),
    ]
    if req.resume_text:
        messages.append(message("user", f"(Resume context)\n{(req.resume_text or '')[:4000]}"))
    messages.append(message("user", context_block))

    # Non-streaming completion
    comp = client.chat.completions.create(
        model=MODEL_CHAT,
        temperature=0.2,
        messages=messages,
    )
    reply = comp.choices[0].message.content or ""
    save_chat_log(req.message, reply)

    # Simple citations surface (headers of retrieved)
    citations = [hdr for hdr, _ in retrieved]
    return ChatResponse(reply=reply, citations=citations)

# Optional: SSE streaming endpoint
@router.get("/chat/stream")
def chat_stream(message: str, resume_text: str = ""):
    def gen() -> Iterator[bytes]:
        retrieved = retrieve(resume_text or "", message or "")
        context_block = build_context_block(resume_text or "", message or "", retrieved)
        messages = [message_fn("system", SYSTEM_PROMPT)]
        if resume_text:
            messages.append(message_fn("user", f"(Resume context)\n{resume_text[:4000]}"))
        messages.append(message_fn("user", context_block))

        stream = client.chat.completions.create(
            model=MODEL_CHAT,
            temperature=0.2,
            messages=messages,
            stream=True,
        )
        partial = ""
        for chunk in stream:
            delta = (chunk.choices[0].delta.content or "")
            if delta:
                partial += delta
                yield f"data: {delta}\n\n".encode("utf-8")
        save_chat_log(message, partial)

    # local helper to avoid shadowing outer "message"
    def message_fn(role, content): return {"role": role, "content": content}

    return StreamingResponse(gen(), media_type="text/event-stream")
