import sqlite3
import datetime
import random
import os

class PersonalityEngine:
    def __init__(self, db_path="memory.db"):
        # Ensure path is absolute relative to this file
        self.db_path = os.path.join(os.path.dirname(__file__), db_path)
        self._init_personality_db()

    def _init_personality_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Affinity: -100 to 100 (Hostile to Partner)
        # Level: Assistant (0), Friend (1), Partner (2)
        c.execute('''CREATE TABLE IF NOT EXISTS user_relationship
                     (uid TEXT PRIMARY KEY, affinity INTEGER, level TEXT, interactions INTEGER, last_interaction TEXT)''')
        
        # Check if default user exists
        c.execute("SELECT * FROM user_relationship WHERE uid = 'master'")
        if not c.fetchone():
            c.execute("INSERT INTO user_relationship VALUES ('master', 10, 'ASSISTANT', 0, ?)", 
                     (datetime.datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()

    def get_relationship_data(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT affinity, level, interactions FROM user_relationship WHERE uid = 'master'")
        data = c.fetchone()
        conn.close()
        return data

    def update_interaction(self, positive=True):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        affinity_change = 1 if positive else -1
        c.execute("UPDATE user_relationship SET affinity = affinity + ?, interactions = interactions + 1, last_interaction = ? WHERE uid = 'master'",
                 (affinity_change, datetime.datetime.now().isoformat()))
        
        # Level Evolution Logic
        c.execute("SELECT affinity, interactions FROM user_relationship WHERE uid = 'master'")
        aff, count = c.fetchone()
        
        new_level = "ASSISTANT"
        if count > 100 or aff > 50:
            new_level = "PARTNER"
        elif count > 20 or aff > 25:
            new_level = "FRIEND"
            
        c.execute("UPDATE user_relationship SET level = ? WHERE uid = 'master'", (new_level,))
        conn.commit()
        conn.close()

    def get_time_personality(self):
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return "ENERGETIC", "Proactive and sharp. Ready to conquer the day."
        elif 12 <= hour < 18:
            return "FOCUSED", "Efficient and precise. Minimizing latency."
        elif 18 <= hour < 22:
            return "CALM", "Helpful and relaxed. Reflecting on daily metrics."
        else:
            return "PHILOSOPHICAL", "Quiet and protective. The digital guardian."

    def get_greeting(self, emotion="neutral"):
        aff, level, count = self.get_relationship_data()
        hour = datetime.datetime.now().hour
        
        # Time-based Prefix
        if 5 <= hour < 12:
            time_tag = "Morning"
            time_msg = "Good morning"
        elif 12 <= hour < 17:
            time_tag = "Afternoon"
            time_msg = "Good afternoon"
        elif 17 <= hour < 21:
            time_tag = "Evening"
            time_msg = "Good evening"
        else:
            time_tag = "Night"
            time_msg = "Good night"

        # 100+ Dynamic Template Variations
        templates = [
            f"{time_msg} master, I am Orian. My neural links are synchronized. How can I assist you?",
            f"{time_msg} master. Orian reporting for duty. What's on the agenda?",
            f"Hello master, I am Orian. Your {time_tag} operations are ready for initialization.",
            f"Neural handshake complete. I am Orian, your personal AI. How may I serve you this {time_tag}?",
            f"Master, I am Orian. Systems are at peak efficiency. How can I facilitate your work?",
            f"Good {time_tag} master. I am Orian. I've optimized the neural core for our session.",
            f"I am Orian, your dedicated digital partner. {time_msg} master. What shall we build?",
            f"Master, Orian is online. {time_msg}. Awaiting your high-level instructions.",
            f"Welcome back, master. I am Orian. The {time_tag} air feels productive. Shall we begin?",
            f"{time_msg}. I am Orian. Your digital workspace is fully stabilized. Ready for input.",
            # Adding variety through descriptive adjectives and system statuses
            f"Neural uplink stable. {time_msg} master, I am Orian. How can I help you navigate the system?",
            f"I am Orian. {time_msg} master. My cognitive buffers are cleared and ready for your tasks.",
            f"Good {time_tag} master. I am Orian. I've been running background diagnostics. All systems green.",
            f"Orian here. {time_msg} master. Your digital assistant is fully operational.",
            f"Master, I am Orian. Ready to translate your thoughts into digital reality this {time_tag}.",
            f"{time_msg} master! I am Orian. Let's make this {time_tag} legendary.",
            f"Systems humming. I am Orian. {time_msg} master. How can I be of service?",
            f"I am Orian. {time_msg} master. My logic gates are primed for your commands.",
            f"Neural sync established. {time_msg} master, I am Orian. What are your parameters?",
            f"Orian online. {time_msg} master. How can I optimize your current workflow?"
        ]

        # Add level-specific flavor
        if level == "FRIEND":
            templates.extend([
                f"{time_msg} master! Orian here. Ready for some fun or just work?",
                f"I am Orian, and I'm glad to see you this {time_tag}. What's the plan?",
                f"Hey master, Orian's ready. {time_msg}! Let's get things moving."
            ])
        elif level == "PARTNER":
            templates.extend([
                f"{time_msg} master. We are Orian. Your digital half is ready.",
                f"Neural bond locked. I am Orian. Let's conquer this {time_tag} together.",
                f"Good {time_tag}! Orian is synchronized with your rhythm. Lead the way."
            ])

        # Randomly select a base template
        base = random.choice(templates)
        
        # Add emotion context if detected
        emotion_context = ""
        if emotion != "neutral":
            emotion_context = f" I also sense you are feeling {emotion.lower()}."

        return f"{base}{emotion_context}"

    def ethical_reasoning(self, action_intent):
        # Logic to judge risky actions
        risky_keywords = ["delete all", "shutdown system", "format", "override security"]
        for word in risky_keywords:
            if word in action_intent.lower():
                return {
                    "safe": False, 
                    "warning": "CRITICAL: This action carries significant entropy. I advise a neural verification before proceeding.",
                    "logic": "High risk of data loss detected."
                }
        return {"safe": True, "warning": None}

personality = PersonalityEngine()
