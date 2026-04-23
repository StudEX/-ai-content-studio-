#!/usr/bin/env python3
"""
Robusca - Unified Desktop & Web App for StudEx Group
Runs as both a desktop app (with UI) and web server (for remote access)

Usage:
    python robusca.py              # Desktop mode
    python robusca.py --web         # Web-only mode (port 8080)
    python robusca.py --voice       # Voice assistant mode
"""

import os
import sys
import asyncio
import json
import platform
import subprocess
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

# Cross-platform imports
try:
    import httpx
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

# Voice imports
try:
    import speech_recognition as sr
    from pyttsx3 import init as pyttsx_init
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Platform detection
SYSTEM = platform.system()
IS_MAC = SYSTEM == "Darwin"
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "app_name": "Robusca",
    "version": "1.0.0",
    "company": "StudEx Group",
    "port": 8080,
    "ollama_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
    "model_default": os.getenv("MODEL_DEFAULT", "qwen2.5-coder:7b"),
    "model_voice": os.getenv("MODEL_VOICE", "phi4-mini"),
    "model_reasoning": os.getenv("MODEL_REASONING", "deepseek-r1:8b"),

    # Slack config
    "slack_bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
    "slack_app_token": os.getenv("SLACK_APP_TOKEN", ""),

    # WhatsApp config
    "whatsapp_number": os.getenv("WHATSAPP_NUMBER", "+27835932577"),

    # AgentMail
    "agentmail_api_key": os.getenv("AGENTMAIL_API_KEY", ""),

    # Paths
    "data_dir": Path.home() / ".robusca",
    "memory_file": Path.home() / ".robusca" / "memory.json",
    "tasks_file": Path.home() / ".robusca" / "tasks.json",
}

# ============================================================================
# MODELS
# ============================================================================

class Message(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = datetime.now()

class Task(BaseModel):
    id: str
    title: str
    description: str
    assigned_to: str  # agent name
    status: str = "pending"  # pending, in_progress, completed
    priority: int = 1
    created: datetime = datetime.now()
    completed: Optional[datetime] = None

class Agent(BaseModel):
    name: str
    title: str
    role: str
    model: str
    status: str = "idle"  # idle, busy, offline
    tasks_completed: int = 0
    monthly_budget: float = 0.0
    current_spend: float = 0.0

# ============================================================================
# AGENTS
# ============================================================================

AGENTS = {
    "robusca": Agent(
        name="Robusca",
        title="Chief Operating Officer",
        role="Oversees all operations, coordinates between agents, handles customer communications",
        model="qwen2.5-coder:7b",
        monthly_budget=500.0
    ),
    "naledi": Agent(
        name="Naledi",
        title="Chief Marketing Officer",
        role="Content creation, social media management, brand voice",
        model="qwen2.5:7b",
        monthly_budget=300.0
    ),
    "techlead": Agent(
        name="TechLead",
        title="Chief Technology Officer",
        role="Engineering, code development, system architecture",
        model="qwen2.5-coder:7b",
        monthly_budget=400.0
    ),
    "alpha": Agent(
        name="Alpha",
        title="Global Markets Analyst",
        role="Trading analysis, market research, financial insights",
        model="deepseek-r1:8b",
        monthly_budget=200.0
    ),
    "mwat": Agent(
        name="Mwat",
        title="Meat Operations Manager",
        role="Inventory, orders, logistics for studexmeat.com",
        model="phi4-mini",
        monthly_budget=150.0
    ),
}

# ============================================================================
# OLLAMA CLIENT
# ============================================================================

class OllamaClient:
    """Client for communicating with Ollama local models."""

    def __init__(self, base_url: str = CONFIG["ollama_url"]):
        self.base_url = base_url
        self.available_models = []

    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                data = response.json()
                self.available_models = [m["name"] for m in data.get("models", [])]
                return self.available_models
            except Exception as e:
                print(f"Error listing models: {e}")
                return []

    async def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        stream: bool = False
    ) -> str:
        """Generate response from Ollama model."""
        model = model or CONFIG["model_default"]
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                data = response.json()
                return data.get("response", "")
            except Exception as e:
                return f"Error: {e}"

    async def chat(self, messages: List[Dict], model: str = None) -> str:
        """Chat with Ollama model using message history."""
        model = model or CONFIG["model_default"]
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                data = response.json()
                return data.get("message", {}).get("content", "")
            except Exception as e:
                return f"Error: {e}"

# ============================================================================
# VOICE ASSISTANT
# ============================================================================

class VoiceAssistant:
    """Voice interface for Robusca using Whisper (STT) and Edge TTS (TTS)."""

    def __init__(self):
        self.recognizer = sr.Recognizer() if VOICE_AVAILABLE else None
        self.tts_engine = pyttsx_init() if VOICE_AVAILABLE else None
        self.ollama = OllamaClient()
        self.listening = False

    def speak(self, text: str):
        """Speak text using TTS."""
        if self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            print(f"[TTS] {text}")

    def listen(self) -> Optional[str]:
        """Listen for voice input and transcribe."""
        if not VOICE_AVAILABLE:
            print("Voice not available. Install: pip install SpeechRecognition pyttsx3")
            return None

        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_whisper(audio)
                print(f"Heard: {text}")
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except Exception as e:
                print(f"Error: {e}")
                return None

    async def voice_loop(self, system_prompt: str = None):
        """Continuous voice interaction loop."""
        system = system_prompt or f"You are {CONFIG['app_name']}, a helpful AI assistant for {CONFIG['company']}."

        print(f"Starting {CONFIG['app_name']} voice assistant. Say 'exit' to quit.")
        self.speak(f"Hello! I'm {CONFIG['app_name']}. How can I help you?")

        messages = [{"role": "system", "content": system}]

        while self.listening:
            user_input = self.listen()
            if user_input:
                if user_input.lower() in ["exit", "quit", "stop"]:
                    self.speak("Goodbye!")
                    break

                messages.append({"role": "user", "content": user_input})
                response = await self.ollama.chat(messages)
                messages.append({"role": "assistant", "content": response})

                self.speak(response)

# ============================================================================
# FASTAPI WEB APP
# ============================================================================

def create_app() -> FastAPI:
    """Create FastAPI web application."""
    app = FastAPI(
        title=CONFIG["app_name"],
        description=f"Unified Desktop & Web App for {CONFIG['company']}",
        version=CONFIG["version"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ollama = OllamaClient()

    # WebSocket connections
    active_connections: List[WebSocket] = []

    @app.get("/")
    async def root():
        return {
            "app": CONFIG["app_name"],
            "version": CONFIG["version"],
            "company": CONFIG["company"],
            "status": "running",
            "agents": list(AGENTS.keys())
        }

    @app.get("/agents")
    async def list_agents():
        return {name: agent.dict() for name, agent in AGENTS.items()}

    @app.get("/models")
    async def list_models():
        models = await ollama.list_models()
        return {"models": models}

    @app.post("/chat")
    async def chat(message: Message):
        messages = [{"role": "system", "content": f"You are {CONFIG['app_name']}."},
                    {"role": "user", "content": message.content}]
        response = await ollama.chat(messages)
        return {"response": response}

    @app.post("/chat/{agent_name}")
    async def chat_agent(agent_name: str, message: Message):
        if agent_name not in AGENTS:
            return {"error": f"Agent {agent_name} not found"}

        agent = AGENTS[agent_name]
        system = f"You are {agent.name}, {agent.title}. {agent.role}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": message.content}
        ]
        response = await ollama.chat(messages, model=agent.model)
        return {"agent": agent_name, "response": response}

    @app.post("/voice")
    async def voice_command(command: str):
        """Process voice command."""
        # TODO: Integrate with voice assistant
        return {"status": "received", "command": command}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        active_connections.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Process message
                response = await ollama.generate(data)
                await websocket.send_text(response)
        except WebSocketDisconnect:
            active_connections.remove(websocket)

    return app

# ============================================================================
# DESKTOP UI (Tkinter - Cross-platform)
# ============================================================================

def run_desktop():
    """Run desktop UI using Tkinter."""
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    import threading

    class RobuscaDesktop:
        def __init__(self, root):
            self.root = root
            self.root.title(f"{CONFIG['app_name']} - {CONFIG['company']}")
            self.root.geometry("1200x800")
            self.ollama = OllamaClient()
            self.setup_ui()

        def setup_ui(self):
            # Menu bar
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)

            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="New Task", command=self.new_task)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.root.quit)

            # Agents menu
            agents_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Agents", menu=agents_menu)
            for name in AGENTS.keys():
                agents_menu.add_command(label=name.title(),
                    command=lambda n=name: self.select_agent(n))

            # Main container
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # Left panel - Agents
            left_frame = ttk.LabelFrame(main_frame, text="Agents", padding="5")
            left_frame.grid(row=0, column=0, sticky=(tk.N, tk.S), padx=5)

            self.agent_list = tk.Listbox(left_frame, height=20, width=20)
            for name, agent in AGENTS.items():
                self.agent_list.insert(tk.END, f"{agent.title}")
            self.agent_list.grid(row=0, column=0)
            self.agent_list.bind('<<ListboxSelect>>', self.on_agent_select)

            # Center panel - Chat
            center_frame = ttk.LabelFrame(main_frame, text="Chat", padding="5")
            center_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5)

            self.chat_display = scrolledtext.ScrolledText(center_frame, height=30, width=60)
            self.chat_display.grid(row=0, column=0, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))

            self.chat_input = ttk.Entry(center_frame, width=50)
            self.chat_input.grid(row=1, column=0, sticky=(tk.E, tk.W), pady=5)
            self.chat_input.bind('<Return>', self.send_message)

            send_btn = ttk.Button(center_frame, text="Send", command=self.send_message)
            send_btn.grid(row=1, column=1, padx=5)

            voice_btn = ttk.Button(center_frame, text="🎤 Voice", command=self.start_voice)
            voice_btn.grid(row=2, column=0, pady=5)

            # Right panel - Tasks
            right_frame = ttk.LabelFrame(main_frame, text="Tasks", padding="5")
            right_frame.grid(row=0, column=2, sticky=(tk.N, tk.S), padx=5)

            self.task_list = tk.Listbox(right_frame, height=20, width=25)
            self.task_list.grid(row=0, column=0)

            # Status bar
            self.status_var = tk.StringVar(value="Ready")
            status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
            status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

            # Configure grid weights
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(1, weight=1)
            main_frame.rowconfigure(0, weight=1)
            center_frame.columnconfigure(0, weight=1)
            center_frame.rowconfigure(0, weight=1)

        def on_agent_select(self, event):
            selection = self.agent_list.curselection()
            if selection:
                idx = selection[0]
                agent_name = list(AGENTS.keys())[idx]
                self.current_agent = agent_name
                agent = AGENTS[agent_name]
                self.status_var.set(f"Selected: {agent.title}")

        def select_agent(self, name):
            self.current_agent = name
            self.status_var.set(f"Selected: {AGENTS[name].title}")

        def send_message(self, event=None):
            message = self.chat_input.get()
            if message:
                self.chat_display.insert(tk.END, f"You: {message}\n")
                self.chat_input.delete(0, tk.END)

                # Send to Ollama in background
                threading.Thread(target=self.get_response, args=(message,), daemon=True).start()

        def get_response(self, message):
            agent_name = getattr(self, 'current_agent', 'robusca')
            agent = AGENTS[agent_name]

            async def _get():
                response = await self.ollama.generate(
                    prompt=message,
                    model=agent.model,
                    system=f"You are {agent.name}, {agent.title}. {agent.role}"
                )
                return response

            response = asyncio.run(_get())

            self.root.after(0, lambda: self.chat_display.insert(
                tk.END, f"{agent.name}: {response}\n\n"
            ))

        def start_voice(self):
            if VOICE_AVAILABLE:
                self.status_var.set("Listening...")
                # TODO: Implement voice in thread
            else:
                messagebox.showwarning("Voice", "Voice not available. Install required packages.")

        def new_task(self):
            # TODO: Task creation dialog
            pass

    root = tk.Tk()
    app = RobuscaDesktop(root)
    root.mainloop()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description=f"{CONFIG['app_name']} - Unified Desktop & Web App")
    parser.add_argument("--web", action="store_true", help="Run as web server only")
    parser.add_argument("--voice", action="store_true", help="Start in voice mode")
    parser.add_argument("--port", type=int, default=CONFIG["port"], help="Port for web server")
    args = parser.parse_args()

    # Ensure data directory exists
    CONFIG["data_dir"].mkdir(exist_ok=True)

    if args.voice:
        # Voice mode
        print(f"Starting {CONFIG['app_name']} in voice mode...")
        assistant = VoiceAssistant()
        assistant.listening = True
        asyncio.run(assistant.voice_loop())

    elif args.web:
        # Web-only mode
        print(f"Starting {CONFIG['app_name']} web server on port {args.port}...")
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=args.port)

    else:
        # Desktop mode (also starts web server in background)
        print(f"Starting {CONFIG['app_name']} desktop app...")
        print(f"Web interface available at http://localhost:{args.port}")

        # Start web server in background thread
        def run_web():
            app = create_app()
            uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")

        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()

        # Run desktop UI
        run_desktop()

if __name__ == "__main__":
    # Check dependencies
    if not BACKEND_AVAILABLE:
        print("Installing missing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install",
                       "fastapi", "uvicorn", "httpx", "pydantic"], check=True)

    main()