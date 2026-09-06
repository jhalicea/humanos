import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional


class HumanOSRuntime:
    def __init__(
        self, vault_base="./HumanOS_Vault", core_path="./core", model="llama3"
    ):
        self.vault_base = Path(vault_base)
        self.core_path = Path(core_path)
        self.model = model
        self.ollama_url = "http://localhost:11434/api/chat"

    @property
    def notebook_path(self) -> Path:
        """Dynamically generates today's markdown notebook file path."""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        filename = now.strftime("%Y-%m-%d.md")

        full_path = self.vault_base / year / month / filename
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path

    def load_system_context(self) -> str:
        """Loads constitution to anchor the model."""
        context = "You are the Mirror layer of HumanOS. You have access to the local Life Notebook.\n\n"
        const_file = self.core_path / "constitution.md"
        if const_file.exists():
            context += (
                f"=== CONSTITUTION ===\n{const_file.read_text(encoding='utf-8')}\n\n"
            )
        return context

    def log_interaction(self, role: str, message: str):
        """Appends a turn to today's markdown notebook file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n**[{timestamp}] {role.upper()}**: {message}\n"
        with open(self.notebook_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def handle_local_commands(self, user_input: str) -> Optional[str]:
        """Intercepts commands like viewing the notebook before hitting Ollama."""
        cleaned = user_input.strip().lower()
        if any(
            keyword in cleaned
            for keyword in ["show me the notebook", "notebook", "life notebook"]
        ):
            if self.notebook_path.exists():
                return f"=== SYSTEM INTERCEPT: TODAY'S NOTEBOOK ===\n\n{self.notebook_path.read_text(encoding='utf-8')}"
            return "Today's notebook file does not exist yet."
        return None

    def query_ollama(self, prompt: str) -> str:
        system_prompt = self.load_system_context()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        req = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("message", {}).get(
                    "content", "Error: No response content."
                )
        except Exception as e:
            return f"Error connecting to local model runtime: {e}"

    def run(self):
        print(f"=== HumanOS Active (Model: {self.model}) ===")
        print(f"Logging to: {self.notebook_path}\n")
        while True:
            try:
                user_input = input("HUMAN: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                self.log_interaction("Human", user_input)

                local_response = self.handle_local_commands(user_input)
                if local_response:
                    response_text = local_response
                else:
                    response_text = self.query_ollama(user_input)

                print(f"MIRROR: {response_text}\n")
                self.log_interaction("Mirror", response_text)

            except KeyboardInterrupt:
                print("\nExiting session.")
                break


if __name__ == "__main__":
    runtime = HumanOSRuntime()
    runtime.run()
