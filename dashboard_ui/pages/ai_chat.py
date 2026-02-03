from nicegui import ui, run
import asyncio
from ..common import Components, Theme
import logging
from dataclasses import dataclass, field
from typing import List, Dict

# Import AI Service (Lazy load to prevent blocking if needed, but simple import is fine)
# We need to make sure we don't init it multiple times or block startup
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.ai_service import AIService

logger = logging.getLogger(__name__)


# --- Chat State ---
@dataclass
class ChatMessage:
    text: str
    is_user: bool
    timestamp: str


class ChatState:
    messages: List[ChatMessage] = field(default_factory=list)
    is_typing: bool = False

    def __init__(self):
        self.messages = []
        self.ai_service = None

    def get_service(self):
        if not self.ai_service:
            try:
                self.ai_service = AIService()
            except Exception as e:
                logger.error(f"Failed to init AI Service: {e}")
                return None
        return self.ai_service


# Global chache for simplicity in this demo (per session ideally)
# For NiceGUI, specific page instances are per client


def render_page(state):
    Components.section_header(
        "AI Assistant", "Ask Gemini about your portfolio and the market", "smart_toy"
    )

    # Initialize page-specific chat state if not present (using nicegui app storage? Or just local closure)
    # Using closure state for this page instance
    chat_history = []

    # Service instance
    ai_service_ref = {"val": None}

    # --- UI Components ---

    with ui.column().classes(
        "w-full h-[calc(100vh-200px)] gap-0 border border-slate-700 rounded-lg overflow-hidden"
    ):
        # 1. Chat Area (Scrollable)
        chat_container = ui.column().classes(
            "w-full flex-grow p-4 overflow-y-auto space-y-4 bg-slate-900/50"
        )

        # 2. Input Area (Fixed at bottom)
        with ui.row().classes(
            "w-full p-4 bg-slate-800 border-t border-slate-700 gap-2 items-center"
        ):
            input_field = (
                ui.input(placeholder='Ask about "Gainers" or "Holdings"...')
                .classes("flex-grow")
                .props("rounded outlined dense dark")
            )
            send_btn = ui.button(icon="send", color="indigo").props("round dense flat")

        def add_message(text, is_user=True):
            with chat_container:
                align = (
                    "ml-auto bg-indigo-600 text-white"
                    if is_user
                    else "mr-auto bg-slate-700 text-slate-200"
                )

                with ui.row().classes(
                    f'w-full {"justify-end" if is_user else "justify-start"}'
                ):
                    with ui.column().classes(f"max-w-[80%] p-3 rounded-xl {align}"):
                        ui.markdown(text).classes("text-sm")

            # Scroll to bottom
            js_scroll = f'document.querySelector(".q-page").scrollTo(0, document.body.scrollHeight)'
            # Better specific scroll: get element id? nicegui handles it often automatically or we can use run_javascript
            # chat_container.scroll_to(percent=1.0) # Need to check nicegui docs, scroll_to usually valid
            # For now relying on user or chat_container end

        async def process_message():
            text = input_field.value
            if not text:
                return

            input_field.value = ""
            add_message(text, is_user=True)

            # Show typing indicator
            with chat_container:
                spinner = ui.spinner("dots", size="sm").classes("ml-2 text-slate-500")

            # Init Service if needed
            if not ai_service_ref["val"]:
                try:
                    ai_service_ref["val"] = AIService()
                except Exception as e:
                    spinner.delete()
                    add_message(f"⚠️ Error initializing AI: {e}", is_user=False)
                    return

            # Call AI (Async)
            try:
                response = await run.io_bound(ai_service_ref["val"].send_message, text)
                spinner.delete()
                add_message(response, is_user=False)
            except Exception as e:
                spinner.delete()
                add_message(f"⚠️ Error: {e}", is_user=False)

        # Bind events
        input_field.on("keydown.enter", process_message)
        send_btn.on("click", process_message)

        # Welcome Message
        add_message(
            "👋 Hi! I'm your Upstox AI Assistant. Ask me anything about the market or your portfolio.",
            is_user=False,
        )
